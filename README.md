# Resumen de Arquitectura: Servicio de Correo Electrónico

## 1.0 Visión General de la Arquitectura

Este documento proporciona una descripción clara y detallada de la arquitectura de software del Servicio de Correo Electrónico. El diseño de este servicio se fundamenta en la necesidad estratégica de contar con una arquitectura desacoplada y robusta para una función empresarial crítica como es la comunicación por correo electrónico. Al separar las responsabilidades y optimizar los flujos de trabajo, el sistema garantiza alta disponibilidad, resiliencia y escalabilidad.

El objetivo principal del servicio es ofrecer una API segura, confiable y de alto rendimiento para el envío de correos electrónicos, soportando tanto operaciones síncronas para confirmación inmediata como asíncronas para manejar grandes volúmenes de solicitudes sin degradar la experiencia del cliente.

El diseño se guía por varios principios arquitectónicos clave que aseguran su eficacia y mantenibilidad:

- **Separación de Responsabilidades**: Cada módulo del sistema (`app`, `db`, `mailer`, `queue_worker`) tiene un propósito único y bien definido. El módulo `app` gestiona la interfaz API, `mailer` se encarga de la comunicación SMTP, `db` maneja la persistencia y `queue_worker` procesa tareas en segundo plano.  
- **Procesamiento Asíncrono**: La implementación de una cola de mensajes en memoria (`queue.Queue`) es fundamental. Permite aceptar solicitudes de forma instantánea y delegar el trabajo intensivo a un proceso en segundo plano.  
- **Configuración Externalizada**: Toda la configuración se gestiona mediante variables de entorno, en línea con *Twelve-Factor App*.  
- **Resiliencia y Tolerancia a Fallos**: La comunicación con el servidor SMTP implementa reintentos automáticos con espera exponencial.

---

## 2.0 Componentes Principales y Módulos

Una estructura modular es la piedra angular del proyecto. La división del código en módulos lógicos permite que cada componente evolucione sin afectar a los demás.

| Módulo/Archivo  | Responsabilidad Principal |
|-----------------|---------------------------|
| `app.py`        | Núcleo FastAPI, expone endpoints (`/send`, `/send_async`, `/health`), gestiona autenticación y arranca la cola/worker. |
| `queue_worker.py` | Implementa `MailQueueWorker`. Extrae tareas de la cola y las procesa en segundo plano. |
| `mailer.py`     | Lógica de comunicación SMTP: construcción de correos, conexión TLS/SSL, autenticación y reintentos. |
| `db.py`         | Persistencia con SQLite, inicializa BD y registra cada envío. Usa `threading.Lock` para seguridad en concurrencia. |
| `config.py`     | Centraliza configuración vía variables de entorno. |
| `models.py`     | Esquemas de datos con Pydantic (`SendRequest`, `SendResponse`). |
| `main.py`       | Punto de entrada, arranca Uvicorn con la app definida en `app.py`. |

---

## 3.0 La Capa de API: Interfaz del Servicio

La API es el único punto de entrada al servicio. Construida con FastAPI, aprovecha Pydantic para imponer un "diseño por contrato".

### Endpoints

- **POST /send**  
  - Envío síncrono.  
  - Espera hasta que el correo se envía al SMTP.  
  - Autenticación: cabecera `X-API-Key`.  
  - Error SMTP → `500` con `SendResponse(ok=False)`.

- **POST /send_async**  
  - Envío asíncrono.  
  - Encola la solicitud y responde de inmediato (`202 Accepted`).  
  - Si la cola está llena → `503 Service Unavailable`.

- **GET /health**  
  - Devuelve `{ "status": "ok" }`.  
  - Público, sin autenticación.  

---

## 4.0 Flujos de Envío de Correo

### Flujo Síncrono
1. Llega POST `/send`.  
2. Se valida `API_KEY`.  
3. `mailer.send_email()` envía el correo (con reintentos).  
4. `db.log_message()` registra el resultado.  
5. Respuesta `200 OK` o `500`.

👉 Confirmación definitiva pero con más latencia.

### Flujo Asíncrono
1. Llega POST `/send_async`.  
2. Se valida `API_KEY`.  
3. El payload se encola (`mail_queue.put_nowait`).  
4. Respuesta inmediata `202 Accepted`.  
5. `MailQueueWorker` procesa en segundo plano.

👉 Menor latencia, mayor resistencia a carga.

---

## 5.0 Procesamiento en Segundo Plano: La Cola y el Worker

- Cola en memoria (`queue.Queue`), tamaño máximo definido por `QUEUE_MAXSIZE`.  
- `MailQueueWorker`:  
  - Arranca en evento `startup` de FastAPI.  
  - Extrae tareas con `q.get(timeout=0.5)`.  
  - Llama a `mailer.send_email` y `db.log_message`.  
  - Captura errores sin detener el hilo.  

---

## 6.0 Módulo de Envío y Resiliencia (Mailer)

- Verificación fail-fast (`SMTP_SERVER` obligatorio).  
- Construcción de mensaje con `MIMEText`.  
- Conexión segura (TLS/SSL).  
- Autenticación SMTP opcional.  
- Manejo de errores → `SmtpError`.  
- Reintentos con `tenacity` (`stop_after_attempt(3)`, `wait_exponential`).  

---

## 7.0 Persistencia de Datos: Registro en Base de Datos

### Esquema SQLite (`mensajes_enviados`)
| Campo       | Tipo     | Descripción |
|-------------|----------|-------------|
| id          | INTEGER  | PK autoincremental |
| subject     | TEXT     | Asunto (NOT NULL) |
| body        | TEXT     | Cuerpo (NOT NULL) |
| timestamp   | DATETIME | Por defecto ahora |
| message_type| TEXT     | Categoría opcional |
| recipient   | TEXT     | Dirección destino |
| success     | INTEGER  | 1=éxito, 0=falla |

- Concurrencia: uso de `_db_lock` (mutex).  
- Múltiples destinatarios → inserta varias filas.  
- `check_same_thread=False` para compartir conexión entre hilos.  

---

## 8.0 Configuración y Despliegue

- Toda config vía **variables de entorno**:  
  - Servicio HTTP: `SERVICE_HOST`, `SERVICE_PORT`  
  - Seguridad: `API_KEY`  
  - SMTP: `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS`  
  - Base de Datos: `DATABASE_DIR`, `DATABASE_NAME`  
  - Cola/Worker: `QUEUE_MAXSIZE`  

- `main.py` arranca Uvicorn con la app FastAPI.  
- Dependencias en `requirements.txt` (ej. fastapi, uvicorn, tenacity).  

---

## 9.0 Conclusión Arquitectónica

El Servicio de Correo Electrónico es:

- **API moderna con FastAPI** → validación automática de datos con Pydantic.  
- **Escalable** gracias al desacoplamiento con la cola.  
- **Resiliente** con reintentos exponenciales en SMTP.  
- **Auditable** con registro exhaustivo en SQLite.  

En conjunto, ofrece un diseño moderno, robusto y preparado para funciones críticas de negocio.