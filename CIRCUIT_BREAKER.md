# Circuit Breaker Implementation

## Overview

El Circuit Breaker es un patrón de diseño que previene fallos en cascada cuando un servicio externo falla o se vuelve lento. Funciona como un interruptor eléctrico: detecta fallos y temporalmente bloquea requests para dar tiempo al servicio a recuperarse.

## Estados del Circuit Breaker

```
┌─────────┐          ┌─────────┐          ┌────────────┐
│ CLOSED  │─────────►│  OPEN   │─────────►│ HALF_OPEN  │
│ (Normal)│  Failure │(Blocking)│  Timeout │  (Testing) │
└────┬────┘ Threshold└─────────┘          └─────┬──────┘
     │        Exceeded                           │
     │                                           │
     │           Success Threshold Met           │
     └───────────────────────────────────────────┘
```

### 1. CLOSED (Cerrado) - Operación Normal
- ✅ Todas las requests pasan al servicio externo
- ✅ Se registran éxitos y fallos
- Si fallos consecutivos ≥ `failure_threshold` → transición a **OPEN**

### 2. OPEN (Abierto) - Servicio Bloqueado
- ⛔ Se bloquean TODAS las requests
- ⛔ Se lanza `CircuitBreakerError` inmediatamente
- ⏰ Después de `recovery_timeout` segundos → transición a **HALF_OPEN**

### 3. HALF_OPEN (Semi-Abierto) - Probando Recuperación
- 🔄 Se permiten requests para probar si el servicio se recuperó
- Si `success_threshold` éxitos consecutivos → transición a **CLOSED**
- Si algún fallo → transición de vuelta a **OPEN**

## Configuración

### Parámetros del Circuit Breaker

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `failure_threshold` | 5 | Fallos consecutivos antes de abrir el circuito |
| `recovery_timeout` | 60.0 | Segundos en estado OPEN antes de intentar recuperación |
| `success_threshold` | 2 | Éxitos consecutivos en HALF_OPEN para cerrar el circuito |
| `expected_exceptions` | `(Exception,)` | Tipos de excepciones consideradas como fallos |

### Ejemplo de Configuración

```python
from utils.circuit_breaker import SimpleCircuitBreaker
import httpx

# Circuit breaker personalizado
breaker = SimpleCircuitBreaker(
    failure_threshold=3,        # Abrir después de 3 fallos
    recovery_timeout=30.0,      # Esperar 30 segundos antes de probar
    success_threshold=2,        # Cerrar después de 2 éxitos
    expected_exceptions=(httpx.HTTPError, TimeoutError)
)
```

## Uso

### 1. Con OpenWeatherMapService (Implementado)

El servicio de clima ya incluye Circuit Breaker por defecto:

```python
from utils.Weather import OpenWeatherMapService

# Con circuit breaker (default)
service = OpenWeatherMapService(
    enable_circuit_breaker=True,
    failure_threshold=5,
    recovery_timeout=60.0
)

try:
    weather = service.get_weather("Madrid", "ES")
except CircuitBreakerError as e:
    print(f"Service temporarily unavailable. Retry after {e.retry_after}s")
```

### 2. Con Decorador

```python
from utils.circuit_breaker import circuit_breaker

@circuit_breaker(failure_threshold=3, recovery_timeout=30.0)
def call_external_api():
    response = requests.get("https://api.example.com/data")
    return response.json()

# Usar la función normalmente
try:
    data = call_external_api()
except CircuitBreakerError:
    # Circuit breaker está OPEN
    data = get_fallback_data()
```

### 3. Directamente

```python
from utils.circuit_breaker import SimpleCircuitBreaker

breaker = SimpleCircuitBreaker()

def risky_operation():
    # Operación que puede fallar
    return external_service.call()

# Ejecutar a través del circuit breaker
try:
    result = breaker.call(risky_operation)
except CircuitBreakerError:
    # Manejar circuit breaker OPEN
    result = fallback_value
```

## Monitoreo

### API Endpoints

#### 1. Ver Estadísticas de Todos los Circuit Breakers

```bash
curl http://localhost:8000/circuit-breaker/stats
```

**Respuesta:**
```json
{
  "openweathermap_api": {
    "state": "closed",
    "failure_count": 0,
    "success_count": 0,
    "total_failures": 3,
    "total_successes": 47,
    "failure_threshold": 5,
    "recovery_timeout": 60.0,
    "success_threshold": 2,
    "success_rate": 0.94
  }
}
```

#### 2. Ver Estadísticas de un Circuit Breaker Específico

```bash
curl http://localhost:8000/circuit-breaker/openweathermap_api/stats
```

#### 3. Listar Todos los Circuit Breakers

```bash
curl http://localhost:8000/circuit-breaker/list
```

**Respuesta:**
```json
{
  "breakers": ["openweathermap_api"],
  "count": 1
}
```

#### 4. Resetear un Circuit Breaker

```bash
curl -X POST http://localhost:8000/circuit-breaker/openweathermap_api/reset
```

**Respuesta:**
```json
{
  "message": "Circuit breaker 'openweathermap_api' reset successfully",
  "state": "closed"
}
```

### Estadísticas Explicadas

```python
{
    "state": "closed",              # Estado actual: closed, open, half_open
    "failure_count": 2,             # Fallos consecutivos actuales
    "success_count": 0,             # Éxitos consecutivos actuales
    "total_failures": 15,           # Total de fallos desde inicio
    "total_successes": 185,         # Total de éxitos desde inicio
    "failure_threshold": 5,         # Threshold configurado
    "recovery_timeout": 60.0,       # Timeout configurado
    "success_threshold": 2,         # Success threshold configurado
    "success_rate": 0.925,          # Tasa de éxito (0.0 - 1.0)
    "last_failure_time": "2025-01-15T14:30:25.123",  # Último fallo
    "opened_at": "2025-01-15T14:30:30.000",          # Cuando se abrió (si OPEN)
    "time_open": 25.5,                               # Segundos en OPEN (si OPEN)
    "retry_after": 34.5                              # Segundos hasta HALF_OPEN (si OPEN)
}
```

## Escenarios de Uso

### Escenario 1: API Externa Temporal

Mente Lenta

```
Time: 14:00:00
Request 1: OpenWeatherMap → 200 OK (success_count=1)
Request 2: OpenWeatherMap → 200 OK (success_count=2)
Request 3: OpenWeatherMap → Timeout (failure_count=1)
Request 4: OpenWeatherMap → Timeout (failure_count=2)
Request 5: OpenWeatherMap → Timeout (failure_count=3)
Request 6: OpenWeatherMap → Timeout (failure_count=4)
Request 7: OpenWeatherMap → Timeout (failure_count=5)

⚠️  Circuit Breaker: CLOSED → OPEN
    Opened at: 14:00:35
    Retry after: 60 seconds

Time: 14:00:36 - 14:01:35
Requests 8-20: CircuitBreakerError (blocked immediately)
                No llamadas al API
                Protege el API y mejora respuesta

Time: 14:01:35
⏰ Circuit Breaker: OPEN → HALF_OPEN

Time: 14:01:36
Request 21: OpenWeatherMap → 200 OK (success_count=1)

Time: 14:01:37
Request 22: OpenWeatherMap → 200 OK (success_count=2)

✅ Circuit Breaker: HALF_OPEN → CLOSED
   Service recovered!
```

### Escenario 2: Fallo Permanente

```
Time: 15:00:00
Circuit: CLOSED
Requests: Todas fallan → Circuit opens

Time: 15:01:00
Circuit: HALF_OPEN
First request: Falla → Circuit reopens

Time: 15:02:00
Circuit: HALF_OPEN again
First request: Falla → Circuit reopens

Continúa intentando cada 60 segundos...
```

## Integración con Repositorios

El Circuit Breaker se integra automáticamente con el `APIWeatherRepository`:

```python
from repositories.weather_repository import APIWeatherRepository, CachedWeatherRepository

# Repository con circuit breaker
repo = APIWeatherRepository(enable_circuit_breaker=True)

# Repository con cache Y circuit breaker
cached_repo = CachedWeatherRepository()
# El repository subyacente tiene circuit breaker activado

# Obtener datos - circuit breaker protege automáticamente
weather = repo.get_by_city("Madrid", "ES")
```

## Beneficios

### 1. Prevención de Fallos en Cascada
- Detiene requests antes de que lleguen al servicio fallido
- Previene que fallos se propaguen a otros componentes
- Protege recursos del sistema

### 2. Respuesta Rápida al Usuario
- CircuitBreakerError inmediato vs esperar timeout (30s+)
- Usuario recibe respuesta en <1ms en lugar de 30s
- Mejor experiencia de usuario

### 3. Dar Tiempo de Recuperación al Servicio
- No bombardea servicio fallido con más requests
- Permite que el servicio se recupere
- Reduce carga en momentos críticos

### 4. Métricas y Visibilidad
- Estadísticas en tiempo real del estado del servicio
- Alertas automáticas cuando circuit abre
- Histórico de fallos y recuperaciones

## Estrategias de Fallback

Cuando el circuit breaker está OPEN, usa estrategias de fallback:

### 1. Datos Cacheados Antiguos

```python
def get_weather_with_fallback(city, country):
    try:
        # Intentar obtener datos frescos
        return weather_repository.get_by_city(city, country)
    except CircuitBreakerError:
        # Circuit breaker OPEN - usar cache antiguo
        log.warning(f"Using stale cache for {city}")
        return get_stale_cache(city, country)
```

### 2. Datos Por Defecto

```python
def get_weather_with_default(city, country):
    try:
        return weather_service.get_weather(city, country)
    except CircuitBreakerError:
        # Retornar datos por defecto
        return {
            "name": city,
            "main": {"temp": None},
            "weather": [{"main": "Unknown", "description": "Service unavailable"}]
        }
```

### 3. Servicio Alternativo

```python
def get_weather_with_backup(city, country):
    try:
        return primary_service.get_weather(city, country)
    except CircuitBreakerError:
        log.info("Primary service down, using backup")
        return backup_service.get_weather(city, country)
```

## Mejores Prácticas

### 1. Configuración Apropiada

```python
# Para APIs críticos con bajo SLA
critical_breaker = SimpleCircuitBreaker(
    failure_threshold=3,        # Abre rápido
    recovery_timeout=120.0,     # Espera más
    success_threshold=3         # Requiere más pruebas
)

# Para APIs menos críticos
standard_breaker = SimpleCircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0,
    success_threshold=2
)

# Para servicios internos rápidos
internal_breaker = SimpleCircuitBreaker(
    failure_threshold=10,       # Más tolerante
    recovery_timeout=30.0,      # Recuperación rápida
    success_threshold=2
)
```

### 2. Logging y Alertas

```python
def monitor_circuit_breaker():
    stats = circuit_breaker_registry.get_all_stats()

    for name, stat in stats.items():
        if stat["state"] == "open":
            # Alert! Circuit breaker abierto
            send_alert(f"Circuit breaker {name} is OPEN!")

        if stat["success_rate"] < 0.9:
            # Warning! Success rate bajo
            send_warning(f"Circuit breaker {name} success rate: {stat['success_rate']}")
```

### 3. Testing

```python
def test_circuit_breaker():
    breaker = SimpleCircuitBreaker(failure_threshold=3)

    # Simular fallos
    for i in range(3):
        try:
            breaker.call(lambda: raise_error())
        except Exception:
            pass

    # Circuit debe estar OPEN
    assert breaker.state == CircuitState.OPEN

    # Debe bloquear siguiente request
    with pytest.raises(CircuitBreakerError):
        breaker.call(lambda: "success")
```

## Troubleshooting

### Problema: Circuit Breaker Abre Frecuentemente

**Causas Posibles:**
- `failure_threshold` demasiado bajo
- Servicio externo inestable
- Timeouts muy cortos

**Solución:**
```python
# Aumentar threshold
service = OpenWeatherMapService(
    failure_threshold=10,  # Más tolerante
    recovery_timeout=120.0  # Espera más
)
```

### Problema: Circuit No Cierra Después de Recuperación

**Causas Posibles:**
- `success_threshold` muy alto
- Servicio aún no completamente recuperado

**Solución:**
```python
# Resetear manualmente si es necesario
curl -X POST http://localhost:8000/circuit-breaker/openweathermap_api/reset
```

### Problema: Muchas CircuitBreakerErrors para Usuarios

**Causas Posibles:**
- No hay estrategia de fallback
- Recovery timeout demasiado largo

**Solución:**
```python
# Implementar fallback
try:
    weather = service.get_weather(city, country)
except CircuitBreakerError:
    # Usar cache antiguo o datos por defecto
    weather = get_cached_data(city, country, allow_stale=True)
```

## Referencias

- [Martin Fowler - Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Microsoft - Circuit Breaker Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)
- [Release It! - Michael Nygard](https://pragprog.com/titles/mnee2/release-it-second-edition/)

## Resumen

El Circuit Breaker protege tu aplicación de fallos en servicios externos:

✅ **Previene fallos en cascada**
✅ **Respuesta rápida al usuario**
✅ **Protege servicios externos**
✅ **Métricas y visibilidad**
✅ **Fácil integración**
✅ **Thread-safe**

Configuración por defecto en OpenWeatherMap:
- **5 fallos** → Circuit OPEN
- **60 segundos** de espera
- **2 éxitos** → Circuit CLOSED

¡Ya está funcionando en tu aplicación! 🎉