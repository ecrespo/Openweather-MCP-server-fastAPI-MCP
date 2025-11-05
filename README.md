
# OpenWeather MCP Server with FastAPI

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.120+-green.svg)](https://fastapi.tiangolo.com/)
[![MCP](https://img.shields.io/badge/MCP-1.20+-orange.svg)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Servidor MCP (Model Context Protocol) construido con FastAPI que proporciona información meteorológica a través de la API de OpenWeatherMap. Implementa el protocolo MCP sobre HTTP con autenticación Bearer token.

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
  - [Ejecutar el Servidor](#ejecutar-el-servidor)
  - [Cliente MCP](#cliente-mcp)
- [API Endpoints](#-api-endpoints)
  - [REST Endpoints](#rest-endpoints)
  - [MCP Endpoints](#mcp-endpoints)
- [Herramientas MCP](#-herramientas-mcp)
- [Autenticación](#-autenticación)
- [Testing](#-testing)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Módulos](#-módulos)
- [Ejemplos](#-ejemplos)
  - [Cliente Python Simple](#ejemplo-1-cliente-python-simple)
  - [Cliente MCP Personalizado](#ejemplo-2-cliente-mcp-personalizado)
  - [Integración con Claude Desktop](#ejemplo-3-integración-con-claude-desktop)
  - [Depuración con MCP Inspector](#ejemplo-4-depuración-con-mcp-inspector)
- [Recursos Adicionales](#-recursos-adicionales)
- [Preguntas Frecuentes (FAQ)](#-preguntas-frecuentes-faq)
- [Troubleshooting](#-troubleshooting)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)
- [Agradecimientos](#-agradecimientos)

## 🚀 Características

### Core Features
- ✅ **Protocolo MCP sobre HTTP**: Implementación completa del protocolo MCP usando JSON-RPC 2.0
- ✅ **API RESTful**: Endpoints REST tradicionales para consultas meteorológicas
- ✅ **Autenticación Bearer Token**: Seguridad mediante tokens de autenticación local
- ✅ **OpenWeatherMap Integration**: Datos meteorológicos en tiempo real

### Architecture & Design Patterns
- ✅ **Dependency Injection Container**: Sistema DI completo con soporte para singletons y transients
- ✅ **Repository Pattern**: Capa de abstracción para acceso a datos con caching
- ✅ **Circuit Breaker Pattern**: Protección contra fallos en cascada con recuperación automática
- ✅ **Protocol-Based Design**: Interfaces claras con Python protocols para máxima flexibilidad

### Logging & Observability
- ✅ **Structured Logging**: Logs estructurados en JSON con Structlog para análisis avanzado
- ✅ **Request Tracing**: Context propagation automático con request_id y user_id
- ✅ **Performance Monitoring**: Medición automática de duración de operaciones
- ✅ **Rich Console Output**: Visualización hermosa con syntax highlighting y colores
- ✅ **Multiple Log Formats**: Console (Rich), archivo texto, JSON estructurado, errores separados
- ✅ **Data Security**: Censura automática de passwords, tokens y API keys en logs

### Testing & Quality
- ✅ **Testing Completo**: Suite de pruebas unitarias con pytest (61 tests passing)
- ✅ **Type Hints**: Código completamente tipado con Python type hints
- ✅ **Configuración Flexible**: Variables de entorno para fácil configuración
- ✅ **Rate Limiting**: Protección contra abuso con slowapi

## 🆕 Novedades — 2025-11-05

Hoy se incorporaron cambios importantes que ya están disponibles en el código y la documentación asociada:

- Logging mejorado con Structlog + Loguru + Rich: logging estructurado (JSON), trazabilidad por request, métricas de desempeño y salida enriquecida en consola. Ver `utils/logger.py` y ejemplos en `examples/structured_logging_example.py`.
- HTTP Client centralizado: nueva clase `HTTPClient` para unificar y testear llamadas HTTP (`utils/http_client.py`).
- Contenedor de Dependencias (DI): `SimpleDIContainer` + helpers para wiring con FastAPI (`utils/container.py`, `utils/dependencies.py`).
- Circuit Breaker: implementación `SimpleCircuitBreaker`, registro global y endpoints de monitoreo (`utils/circuit_breaker.py`, rutas en `main.py`).
- Repositorios: `CachedWeatherRepository` para caching de respuestas y capa de acceso a datos (`repositories/weather_repository.py`).
- Protocolos: interfaces tipadas para breaker, config, repositorios y clima (`protocols/*`).
- Rate limiting con `slowapi`: límites globales/por-endpoint integrados vía dependencias (`utils/dependencies.py`).

Documentación ampliada:
- Ver guías dedicadas: `CIRCUIT_BREAKER.md`, `DI_CONTAINER.md`, `REPOSITORY_SUMMARY.md`, `PROTOCOLS_SUMMARY.md`, `ARCHITECTURE.md`, `IMPLEMENTATION_GUIDE.md`.
- Nuevos endpoints documentados en la sección API (coordenadas, cache y circuit breaker).

## 🏗️ Arquitectura

```
┌─────────────────┐
│   MCP Client    │
│  (Claude, etc)  │
└────────┬────────┘
         │ HTTP/JSON-RPC
         ▼
┌─────────────────────────────┐
│   FastAPI MCP Server        │
│  ┌──────────────────────┐   │
│  │  Authentication      │   │
│  │  (Bearer Token)      │   │
│  └──────────────────────┘   │
│  ┌──────────────────────┐   │
│  │  MCP Protocol        │   │
│  │  - initialize        │   │
│  │  - tools/list        │   │
│  │  - tools/call        │   │
│  └──────────────────────┘   │
│  ┌──────────────────────┐   │
│  │  Weather Tools       │   │
│  └──────────────────────┘   │
└──────────┬──────────────────┘
           │ HTTPS
           ▼
┌─────────────────────────────┐
│   OpenWeatherMap API        │
└─────────────────────────────┘
```

## 📦 Requisitos

- Python 3.13+
- OpenWeatherMap API Key
- uv (gestor de paquetes recomendado) o pip

## 🔧 Instalación

### Usando uv (Recomendado)

```bash
# Clonar el repositorio
git clone https://github.com/yourusername/Openweather-MCP-server-fastAPI-MCP.git
cd Openweather-MCP-server-fastAPI-MCP

# Instalar dependencias
uv sync
```

### Usando pip

```bash
# Clonar el repositorio
git clone https://github.com/yourusername/Openweather-MCP-server-fastAPI-MCP.git
cd Openweather-MCP-server-fastAPI-MCP

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -e .
```

## ⚙️ Configuración

Crear un archivo `.env` en la raíz del proyecto:

```env
# OpenWeatherMap Configuration
ACCESS_KEY=your_openweathermap_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=1
RELOAD=false

# Authentication
LOCAL_TOKEN=your_secret_token_here
URL=http://localhost:8000

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=./logs/mcp_server.log
LOG_ROTATION=10 MB
LOG_RETENTION=7 days

# Session Configuration
SESSION_TIMEOUT=3600
SESSION_CLEANUP_INTERVAL=300
```

### Variables de Entorno Requeridas

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `ACCESS_KEY` | API key de OpenWeatherMap | `abc123def456...` |
| `LOCAL_TOKEN` | Token para autenticación del servidor | `my-secret-token-123` |
| `URL` | URL base del servidor | `http://localhost:8000` |

### Variables de Entorno Opcionales

| Variable | Default | Descripción |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host del servidor |
| `PORT` | `8000` | Puerto del servidor |
| `WORKERS` | `1` | Número de workers de Uvicorn |
| `RELOAD` | `false` | Auto-reload en desarrollo |
| `LOG_LEVEL` | `INFO` | Nivel de logging |
| `LOG_FILE` | `./logs/mcp_server.log` | Archivo de logs |
| `LOG_ROTATION` | `10 MB` | Rotación de logs |
| `LOG_RETENTION` | `7 days` | Retención de logs |
| `SESSION_TIMEOUT` | `3600` | Timeout de sesión (segundos) |
| `SESSION_CLEANUP_INTERVAL` | `300` | Intervalo de limpieza (segundos) |

## 💻 Uso

### Ejecutar el Servidor

```bash
# Con uv
uv run python3 main.py

# Con python directamente (después de activar el venv)
python main.py
```

El servidor estará disponible en `http://localhost:8000`

### Cliente MCP

Para probar el servidor usando el cliente MCP incluido:

```bash
# Con uv
uv run python3 weather_mcp_client.py

# Con python directamente
python weather_mcp_client.py
```

El cliente ejecutará automáticamente:
1. Health check del servidor
2. Inicialización de sesión MCP
3. Listado de herramientas disponibles
4. Llamada de ejemplo a la herramienta de clima

## 📡 API Endpoints

### REST Endpoints

#### GET /

Health check del servidor.

**Respuesta:**
```json
"Hello World!"
```

#### GET /weather/{city}/{country}

Obtiene información meteorológica para una ciudad específica.

**Parámetros:**
- `city` (string): Nombre de la ciudad
- `country` (string, opcional): Código de país ISO 3166-1 alpha-2

**Ejemplo:**
```bash
curl http://localhost:8000/weather/London/GB
```

**Respuesta:**
```json
{
  "coord": {"lon": -0.1257, "lat": 51.5085},
  "weather": [
    {
      "id": 800,
      "main": "Clear",
      "description": "cielo claro",
      "icon": "01d"
    }
  ],
  "main": {
    "temp": 20.0,
    "feels_like": 19.5,
    "temp_min": 18.0,
    "temp_max": 22.0,
    "pressure": 1013,
    "humidity": 60
  },
  "name": "London",
  "cod": 200
}
```

#### GET /weather/coordinates/{latitude}/{longitude}

Obtiene información meteorológica por coordenadas geográficas.

- `latitude` (float): -90 a 90
- `longitude` (float): -180 a 180

Ejemplo:
```bash
echo "Consulta por coordenadas"
curl "http://localhost:8000/weather/coordinates/40.4168/-3.7038"
```

#### GET /weather/history/{city}

Histórico de consultas para una ciudad. Útil para depuración y estadísticas locales.

Parámetros query opcionales:
- `country` (string): Código de país ISO 3166-1 alpha-2
- `limit` (int): Número máximo de registros (por defecto 10)

Ejemplo:
```bash
curl "http://localhost:8000/weather/history/Madrid?country=ES&limit=5"
```

#### GET /cache/stats

Estadísticas de la caché del repositorio de clima.

```bash
curl http://localhost:8000/cache/stats
```

#### POST /cache/clear

Limpia la caché del repositorio de clima.

```bash
curl -X POST http://localhost:8000/cache/clear
```

#### GET /circuit-breaker/stats

Estadísticas globales de todos los circuit breakers registrados.

```bash
curl http://localhost:8000/circuit-breaker/stats
```

#### GET /circuit-breaker/{name}/stats

Estadísticas de un circuit breaker específico.

```bash
curl http://localhost:8000/circuit-breaker/openweather/stats
```

#### POST /circuit-breaker/{name}/reset

Reinicia el circuit breaker a estado CLOSED.

```bash
curl -X POST http://localhost:8000/circuit-breaker/openweather/reset
```

#### GET /circuit-breaker/list

Lista de circuit breakers disponibles.

```bash
curl http://localhost:8000/circuit-breaker/list
```

### MCP Endpoints

#### POST /mcp

Endpoint principal del protocolo MCP. Soporta JSON-RPC 2.0.

**Headers requeridos:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

#### Método: initialize

Inicializa una sesión MCP.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "weather-client",
      "version": "1.0.0"
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "serverInfo": {
      "name": "Weather MCP Server",
      "version": "1.0.0"
    }
  }
}
```

#### Método: tools/list

Lista las herramientas MCP disponibles.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "get_weather_by_country",
        "description": "Retrieves weather data for a given city...",
        "inputSchema": {
          "type": "object",
          "properties": {
            "city": {"type": "string"},
            "country": {"type": "string"}
          },
          "required": ["city"]
        }
      }
    ]
  }
}
```

#### Método: tools/call

Ejecuta una herramienta MCP.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "get_weather_by_country",
    "arguments": {
      "city": "Caracas",
      "country": "VE"
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Weather data for Caracas..."
      }
    ]
  }
}
```

## 🛠️ Herramientas MCP

### get_weather_by_country

Obtiene datos meteorológicos para una ciudad y país específicos.

**Parámetros:**
- `city` (string, requerido): Nombre de la ciudad
- `country` (string, opcional): Código de país ISO 3166-1 alpha-2

**Ejemplo de uso:**
```python
{
  "name": "get_weather_by_country",
  "arguments": {
    "city": "Madrid",
    "country": "ES"
  }
}
```

## 🔐 Autenticación

El servidor utiliza autenticación Bearer Token. Todas las llamadas MCP deben incluir el header:

```
Authorization: Bearer <LOCAL_TOKEN>
```

### Configuración del Token

1. Define `LOCAL_TOKEN` en tu archivo `.env`
2. Usa el mismo token en el cliente:

```python
headers = {
    "Authorization": "Bearer <LOCAL_TOKEN>",
    "Content-Type": "application/json"
}
```

### Respuestas de Autenticación

- **200 OK**: Token válido
- **401 Unauthorized**: Token inválido o expirado
- **403 Forbidden**: Token faltante

## 🧪 Testing

El proyecto incluye una suite completa de pruebas unitarias.

### Ejecutar Todas las Pruebas

```bash
# Con uv
uv run python3 -m pytest tests/ -v

# Con pytest directamente
pytest tests/ -v
```

### Ejecutar Pruebas Específicas

```bash
# Solo pruebas de endpoints REST
uv run python3 -m pytest tests/test_main.py::test_weather_success -v

# Solo pruebas de MCP
uv run python3 -m pytest tests/test_main.py -k "mcp" -v
```

### Coverage

```bash
# Instalar pytest-cov
uv add --dev pytest-cov

# Ejecutar con coverage
uv run python3 -m pytest tests/ --cov=. --cov-report=html
```

### Resultados de Pruebas

```
tests/test_main.py::test_weather_success ✓
tests/test_main.py::test_weather_not_found ✓
tests/test_main.py::test_hello_world ✓
tests/test_main.py::test_weather_endpoint_via_http ✓
tests/test_main.py::test_mcp_initialize_with_auth ✓
tests/test_main.py::test_mcp_initialize_without_auth ✓
tests/test_main.py::test_mcp_initialize_with_invalid_token ✓
tests/test_main.py::test_mcp_list_tools_without_auth ✓
tests/test_main.py::test_mcp_call_tool_without_auth ✓

9 passed, 6 skipped in 1.04s
```

**Nota:** Algunas pruebas MCP se saltan debido a limitaciones conocidas de TestClient con task groups async.

## 📁 Estructura del Proyecto

```
Openweather-MCP-server-fastAPI-MCP/
├── main.py                      # Servidor FastAPI con MCP
├── weather_mcp_client.py        # Cliente MCP de prueba
├── pyproject.toml               # Configuración del proyecto
├── .env                         # Variables de entorno (no versionado)
├── README.md                    # Este archivo
│
├── utils/                       # Módulos utilitarios
│   ├── __init__.py
│   ├── auth.py                  # Autenticación y validación de tokens
│   ├── config.py                # Configuración y settings
│   ├── logger.py                # Sistema de logging
│   └── Weather.py               # Módulo de clima y dataclasses
│
└── tests/                       # Suite de pruebas
    ├── __init__.py
    ├── test_main.py             # Pruebas del servidor
    └── test_Weather.py          # Pruebas del módulo Weather
```

## 📚 Módulos

### main.py

Servidor principal FastAPI que:
- Expone endpoints REST para clima
- Implementa el protocolo MCP sobre HTTP
- Gestiona autenticación Bearer token
- Maneja sesiones MCP

**Funciones principales:**
- `hello_world()`: Health check
- `weather(city, country)`: Endpoint REST de clima
- `authenticate_request()`: Dependency para autenticación

### weather_mcp_client.py

Cliente HTTP para conectarse al servidor MCP.

**Métodos disponibles (resumen):**
- `health_check()`
- `initialize()`
- `list_tools()`
- `call_tool(tool_name, arguments)`
- `close()`

### utils/auth.py

Sistema de autenticación con dos clases:

**LocalTokenValidator:**
- Valida tokens contra el token local
- Retorna información del token

**LocalTokenClient:**
- Obtiene el token local para clientes
- Usado por el cliente MCP

### utils/config.py

Gestión de configuración mediante `python-decouple`.

**Clase Settings:**
```python
class Settings:
    ACCESS_KEY: str      # OpenWeatherMap API key
    LOCAL_TOKEN: str     # Token de autenticación
    URL: str             # URL base del servidor
    HOST: str            # Host del servidor
    PORT: int            # Puerto del servidor
    # ... más configuraciones
```

### utils/logger.py

Sistema de logging avanzado con Rich.

**Funciones disponibles:**
- `log`: Logger principal (loguru)
- `console`: Console de Rich
- `log_section()`: Secciones visuales
- `log_table()`: Tablas formateadas
- `log_json()`: JSON con syntax highlighting
- `log_panel()`: Paneles de información
- `log_status()`: Spinner de estado
- `LogContext`: Context manager para logging

### utils/Weather.py

Módulo de clima con integración OpenWeatherMap.

**Dataclass:**
```python
@dataclass
class Weather:
    coord: Dict[str, Any]
    weather: List[Dict[str, Any]]
    main: Dict[str, Any]
    name: str
    # ... más campos
```

**Función principal:**
```python
def weather_request(city: str, country: Optional[str] = None) -> Weather
```

## 💡 Ejemplos

### Ejemplo 1: Cliente Python Simple

```python
import httpx

async def get_weather():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/weather/Paris/FR"
        )
        print(response.json())

# asyncio.run(get_weather())
```

### Ejemplo 2: Cliente MCP Personalizado

```python
from weather_mcp_client import MCPClientHTTP

async def main():
    client = MCPClientHTTP("http://localhost:8000")

    # Inicializar
    await client.initialize()

    # Listar herramientas
    tools = await client.list_tools()
    print(tools)

    # Llamar herramienta
    result = await client.call_tool(
        "get_weather_by_country",
        {"city": "Tokyo", "country": "JP"}
    )
    print(result)

    await client.close()

# asyncio.run(main())
```

### Ejemplo 3: Integración con Claude Desktop

#### Opción 1: Usando uvx (Recomendado)

Configurar en el archivo de configuración de Claude Desktop (`claude_desktop_config.json`):

**Ubicación del archivo:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "weather": {
      "command": "uvx",
      "args": [
        "--from",
        ".",
        "python",
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000"
      ],
      "cwd": "/absolute/path/to/Openweather-MCP-server-fastAPI-MCP",
      "env": {
        "ACCESS_KEY": "your_openweathermap_api_key",
        "LOCAL_TOKEN": "your_secret_token"
      }
    }
  }
}
```

#### Opción 2: Usando uv run

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000"
      ],
      "cwd": "/absolute/path/to/Openweather-MCP-server-fastAPI-MCP",
      "env": {
        "ACCESS_KEY": "your_openweathermap_api_key",
        "LOCAL_TOKEN": "your_secret_token"
      }
    }
  }
}
```

#### Opción 3: Usando Python directamente

```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": [
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000"
      ],
      "cwd": "/absolute/path/to/Openweather-MCP-server-fastAPI-MCP",
      "env": {
        "ACCESS_KEY": "your_openweathermap_api_key",
        "LOCAL_TOKEN": "your_secret_token"
      }
    }
  }
}
```

**Notas importantes:**
- Reemplaza `/absolute/path/to/Openweather-MCP-server-fastAPI-MCP` con la ruta completa a tu proyecto
- Usa `127.0.0.1` en lugar de `0.0.0.0` para mayor seguridad en entornos locales
- Asegúrate de que las variables `ACCESS_KEY` y `LOCAL_TOKEN` sean correctas
- Reinicia Claude Desktop después de modificar la configuración

### Ejemplo 4: Depuración con MCP Inspector

El MCP Inspector es una herramienta oficial para probar y depurar servidores MCP.

#### Instalación y Uso

```bash
# Primero, inicia tu servidor en una terminal
uv run python3 main.py

# En otra terminal, ejecuta el inspector
npx @modelcontextprotocol/inspector@latest http://localhost:8000/mcp
```

#### Uso del Inspector

1. **Abrir el Inspector**: El comando abrirá automáticamente tu navegador en `http://localhost:5173`

2. **Configurar Autenticación**:
   - Click en el ícono de configuración ⚙️
   - En "Headers", agrega:
     ```
     Authorization: Bearer your_secret_token_here
     ```

3. **Probar el Servidor**:
   - **Initialize**: Click en "Connect" para inicializar la sesión
   - **List Tools**: Verás la herramienta `get_weather_by_country`
   - **Call Tool**: Prueba la herramienta con:
     ```json
     {
       "city": "London",
       "country": "GB"
     }
     ```

4. **Ver Respuestas**: El inspector mostrará las respuestas JSON-RPC en tiempo real

#### Opciones Avanzadas del Inspector

```bash
# Especificar puerto personalizado del inspector
npx @modelcontextprotocol/inspector@latest http://localhost:8000/mcp --port 3000

# Con variables de entorno
LOCAL_TOKEN=your_token npx @modelcontextprotocol/inspector@latest http://localhost:8000/mcp
```

#### Captura de Pantalla del Inspector

El inspector muestra:
- 📋 **Tools**: Lista de herramientas disponibles
- 🔧 **Test Tool**: Interfaz para probar cada herramienta
- 📊 **Request/Response**: Detalles de las llamadas JSON-RPC
- 📝 **Logs**: Registro de todas las interacciones

**Ejemplo de prueba exitosa:**

```
Request:
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_weather_by_country",
    "arguments": {
      "city": "Paris",
      "country": "FR"
    }
  }
}

Response:
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Weather in Paris: 15°C, Clear sky..."
      }
    ]
  }
}
```

## 📚 Recursos Adicionales

### Documentación Oficial

- **MCP Protocol**: [https://modelcontextprotocol.io/](https://modelcontextprotocol.io/)
- **MCP Specification**: [https://spec.modelcontextprotocol.io/](https://spec.modelcontextprotocol.io/)
- **FastAPI**: [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
- **OpenWeatherMap API**: [https://openweathermap.org/api](https://openweathermap.org/api)
- **uv Documentation**: [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)

### Herramientas MCP

- **MCP Inspector**: [https://github.com/modelcontextprotocol/inspector](https://github.com/modelcontextprotocol/inspector)
- **Claude Desktop**: [https://claude.ai/download](https://claude.ai/download)
- **MCP Servers**: [https://github.com/modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)

### Tutoriales y Ejemplos

- **MCP Quickstart**: [https://modelcontextprotocol.io/quickstart](https://modelcontextprotocol.io/quickstart)
- **Building MCP Servers**: [https://modelcontextprotocol.io/docs/building-servers](https://modelcontextprotocol.io/docs/building-servers)
- **FastAPI MCP Integration**: [https://github.com/jlowin/fastapi-mcp](https://github.com/jlowin/fastapi-mcp)

### Videos y Contenido

- **MCP Introduction**: Explica los conceptos básicos del protocolo
- **Building Weather Tools**: Tutorial de construcción de herramientas meteorológicas
- **Claude Desktop Setup**: Configuración paso a paso

### Comunidad

- **MCP Discord**: Únete a la comunidad de desarrolladores MCP
- **FastAPI Discord**: Soporte y discusiones sobre FastAPI
- **GitHub Discussions**: Comparte ideas y preguntas en las discusiones del proyecto

### Proyectos Relacionados

Otros servidores MCP que podrían interesarte:

- **mcp-server-fetch**: Servidor MCP para web scraping
- **mcp-server-filesystem**: Servidor MCP para operaciones de archivos
- **mcp-server-git**: Servidor MCP para operaciones Git
- **mcp-server-sqlite**: Servidor MCP para bases de datos SQLite

### Casos de Uso

Este servidor puede ser útil para:

1. **Asistentes AI con Contexto Meteorológico**: Integra información del clima en conversaciones con Claude
2. **Automatización de Viajes**: Consulta el clima antes de planificar viajes
3. **Dashboards Personalizados**: Crea dashboards que combinen datos de múltiples fuentes
4. **Notificaciones de Clima**: Sistema de alertas basado en condiciones meteorológicas
5. **Análisis de Datos**: Combina datos meteorológicos con otros datasets para análisis

## ❓ Preguntas Frecuentes (FAQ)

### ¿Qué es MCP?

MCP (Model Context Protocol) es un protocolo abierto desarrollado por Anthropic que permite a aplicaciones de IA conectarse con fuentes de datos externas y herramientas. Piensa en ello como un "USB para IA" - un estándar que permite que diferentes sistemas se comuniquen de forma sencilla.

### ¿Por qué FastAPI para MCP?

FastAPI ofrece:
- Alto rendimiento similar a NodeJS y Go
- Validación automática de datos con Pydantic
- Documentación automática con OpenAPI
- Type hints nativos de Python
- Soporte async/await nativo

### ¿Necesito Claude Desktop para usar este servidor?

No. Este servidor MCP puede usarse de múltiples formas:
- Con Claude Desktop (recomendado para uso interactivo)
- Con el MCP Inspector (para desarrollo y pruebas)
- Con cualquier cliente HTTP que soporte JSON-RPC
- Como API REST tradicional

### ¿Puedo agregar más herramientas meteorológicas?

¡Sí! Para agregar una nueva herramienta:

1. Agrega el endpoint en `main.py`:
   ```python
   @app.get("/forecast/{city}")
   async def get_forecast(city: str):
       # Tu lógica aquí
       pass
   ```

2. Inclúyela en la lista de operaciones MCP:
   ```python
   mcp = FastApiMCP(
       app,
       include_operations=["get_weather_by_country", "get_forecast"],
       # ...
   )
   ```

3. La herramienta estará automáticamente disponible en MCP

### ¿Cómo obtengo una API key de OpenWeatherMap?

1. Visita [https://openweathermap.org/api](https://openweathermap.org/api)
2. Crea una cuenta gratuita
3. Ve a tu perfil → API keys
4. Copia tu API key
5. Agrégala al archivo `.env` como `ACCESS_KEY`

La cuenta gratuita incluye:
- 1,000 llamadas/día
- Datos actuales del clima
- Pronósticos de 5 días

### ¿Puedo usar este servidor en producción?

Sí, pero considera:

1. **Seguridad:**
   - Cambia `LOCAL_TOKEN` por un token seguro
   - Usa HTTPS en producción
   - Implementa rate limiting
   - Agrega más validaciones de entrada

2. **Escalabilidad:**
   - Aumenta el número de workers
   - Usa un load balancer
   - Implementa caching de respuestas
   - Considera usar Redis para sesiones

3. **Monitoring:**
   - Agrega métricas (Prometheus, Grafana)
   - Implementa alertas
   - Monitorea el uso de la API de OpenWeatherMap

### ¿Cómo actualizo el servidor?

```bash
# Pull los cambios más recientes
git pull origin main

# Actualizar dependencias
uv sync

# Reiniciar el servidor
# Si usas systemd o similar, reinicia el servicio
# Si es manual, detén el proceso actual y ejecuta:
uv run python3 main.py
```

### ¿Puedo usar otros proveedores de clima?

Sí. Solo necesitas:

1. Modificar `utils/Weather.py` para adaptarlo a la nueva API
2. Actualizar las funciones de request
3. Ajustar el dataclass `Weather` según los datos que devuelve la nueva API

Proveedores alternativos:
- WeatherAPI.com
- Weatherbit
- AccuWeather
- Visual Crossing

### ¿Cuánto cuesta ejecutar esto?

El servidor en sí es gratuito. Los únicos costos potenciales son:

- **OpenWeatherMap API**: Plan gratuito disponible, planes pagos desde $40/mes
- **Hosting**: Si lo despliegas en cloud (AWS, GCP, Azure, etc.)
- **Dominio**: Si quieres un dominio personalizado (~$10/año)

Para desarrollo local, es completamente gratuito.

### ¿Funciona con otros LLMs además de Claude?

Sí, el protocolo MCP es agnóstico del modelo. Puede usarse con:
- Claude Desktop (soporte oficial)
- Cualquier LLM que implemente el cliente MCP
- Aplicaciones personalizadas usando el cliente Python incluido

### ¿Puedo combinar múltiples servidores MCP?

Sí, Claude Desktop puede conectarse a múltiples servidores MCP simultáneamente:

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": ["run", "python", "-m", "uvicorn", "main:app", ...],
      "cwd": "/path/to/weather-server"
    },
    "database": {
      "command": "npx",
      "args": ["mcp-server-sqlite", "/path/to/db.sqlite"],
    },
    "files": {
      "command": "npx",
      "args": ["mcp-server-filesystem", "/Users/username/Documents"]
    }
  }
}
```

### ¿Hay límites en el número de llamadas?

El servidor no impone límites, pero ten en cuenta:
- Límites de la API de OpenWeatherMap (1,000 llamadas/día en plan gratuito)
- Límites de tu infraestructura (CPU, memoria, red)
- Para producción, considera implementar rate limiting con:
  - `slowapi` para FastAPI
  - Redis para tracking de límites
  - Nginx para rate limiting a nivel de proxy

## 🔍 Troubleshooting

### Error: "Module not found"

```bash
# Reinstalar dependencias
uv sync --reinstall
```

### Error: "Unauthorized"

Verificar que:
1. El `.env` tenga `LOCAL_TOKEN` configurado
2. El cliente use el mismo token en el header `Authorization`
3. En Claude Desktop, el token en `env.LOCAL_TOKEN` coincida con el del servidor

### Error: "Task group not initialized"

Este es un problema conocido con TestClient y task groups de MCP. Las pruebas afectadas se saltan automáticamente. El servidor funciona correctamente en producción.

### Error: "City not found"

Verificar que:
1. El `ACCESS_KEY` de OpenWeatherMap sea válido
2. El nombre de la ciudad sea correcto
3. El código de país sea ISO 3166-1 alpha-2

### Logs no aparecen

Verificar que el directorio `logs/` exista o que `LOG_FILE` apunte a una ubicación válida.

### Claude Desktop no conecta al servidor

1. **Verificar la configuración:**
   ```bash
   # Verificar que el archivo existe
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json  # macOS
   cat ~/.config/Claude/claude_desktop_config.json  # Linux
   ```

2. **Probar el comando manualmente:**
   ```bash
   cd /absolute/path/to/Openweather-MCP-server-fastAPI-MCP
   uv run python -m uvicorn main:app --host 127.0.0.1 --port 8000
   ```

3. **Ver logs de Claude Desktop:**
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`
   - Linux: `~/.config/Claude/logs/`

4. **Reiniciar Claude Desktop** después de cambios en la configuración

### MCP Inspector no conecta

1. **Verificar que el servidor esté corriendo:**
   ```bash
   curl http://localhost:8000/
   # Debe devolver "Hello World!"
   ```

2. **Verificar el endpoint MCP:**
   ```bash
   curl -X POST http://localhost:8000/mcp \
     -H "Authorization: Bearer your_token" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
   ```

3. **Problemas de CORS:**
   Si el inspector muestra errores de CORS, el servidor ya incluye configuración para permitir todas las origins en desarrollo.

4. **Puerto ocupado:**
   ```bash
   # Verificar qué proceso usa el puerto 8000
   lsof -i :8000  # macOS/Linux
   netstat -ano | findstr :8000  # Windows

   # Usar otro puerto
   uv run python3 main.py  # Cambia PORT en .env
   ```

### Error: "Command not found: uvx" o "Command not found: uv"

```bash
# Instalar uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# O con pip
pip install uv

# Verificar instalación
uv --version
uvx --version
```

### Error: Puerto 8000 ya en uso

```bash
# Opción 1: Cambiar el puerto en .env
echo "PORT=8001" >> .env

# Opción 2: Matar el proceso que usa el puerto
# En Linux/macOS
lsof -ti:8000 | xargs kill -9

# En Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Inspector muestra "Invalid JSON-RPC response"

Verificar que:
1. El servidor esté ejecutándose correctamente
2. La URL en el inspector sea `http://localhost:8000/mcp` (con `/mcp`)
3. El header `Authorization` esté configurado correctamente
4. El token sea válido

### Claude Desktop muestra error "MCP server exited"

Posibles causas:
1. **Variables de entorno faltantes:**
   - Verificar que `ACCESS_KEY` esté en la config
   - Verificar que `LOCAL_TOKEN` esté en la config

2. **Ruta incorrecta:**
   - El `cwd` debe ser la ruta absoluta al proyecto
   - Verificar con: `cd /path/from/config && ls main.py`

3. **Dependencias no instaladas:**
   ```bash
   cd /path/to/project
   uv sync
   ```

4. **Ver logs del servidor:**
   ```bash
   # Los logs de MCP en Claude Desktop están en:
   ~/Library/Logs/Claude/mcp*.log
   ```

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Guía de Contribución

- Seguir PEP 8 para estilo de código
- Agregar type hints a todas las funciones
- Escribir docstrings para clases y funciones
- Agregar pruebas para nuevas funcionalidades
- Actualizar el README si es necesario

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🙏 Agradecimientos

- [FastAPI](https://fastapi.tiangolo.com/) - Framework web moderno
- [MCP](https://modelcontextprotocol.io/) - Model Context Protocol
- [OpenWeatherMap](https://openweathermap.org/) - API de datos meteorológicos
- [Rich](https://rich.readthedocs.io/) - Logging y terminal mejorados
- [Loguru](https://loguru.readthedocs.io/) - Logging simplificado

## 📞 Contacto

Para preguntas o sugerencias, por favor abre un issue en GitHub.

---

**Desarrollado con ❤️ usando FastAPI y MCP**
