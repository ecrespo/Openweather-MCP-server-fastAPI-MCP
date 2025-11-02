import asyncio
import httpx
from utils.logger import (
    log,
    console,
    log_section,
    log_table,
    log_json,
    log_panel,
    log_status,
    LogContext
)
from utils.config import settings
from utils.auth import LocalTokenClient


class MCPClientHTTP:
    """Cliente para conectarse al servidor MCP vía HTTP/SSE"""

    def __init__(self, base_url: str = None):
        # Usar la URL desde configuración por defecto
        self.base_url = base_url or settings.URL.rstrip("/")
        self.session_id = None  # El servidor proporcionará el session_id

        # Preparar autenticación Bearer con el token local
        token_client = LocalTokenClient()
        token = token_client.get_token()
        # Configurar cabeceras: Content-Type y Accept para cumplir con fastapi-mcp
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        else:
            log.warning("No se encontró LOCAL_TOKEN en configuración; las llamadas MCP requerirán autenticación")

        self.client = httpx.AsyncClient(timeout=30.0, headers=self.headers)

        log_panel(
            f"Cliente MCP inicializado\n"
            f"URL: {self.base_url}",
            title="🚀 Cliente MCP",
            style="green"
        )

    async def health_check(self):
        """Verifica el estado del servidor (usa "/" expuesto por FastAPI)"""
        url = f"{self.base_url}/"

        with log_status("Verificando salud del servidor..."):
            try:
                response = await self.client.get(url)
                # Puede devolver texto simple "Hello World!"
                try:
                    result = response.json()
                except Exception:
                    result = {"message": response.text}

                log_json(result, "✅ Estado del Servidor")

                return result
            except Exception as e:
                log.error(f"❌ Error en health check: {e}")
                return None

    async def initialize(self):
        """Inicializa la sesión MCP según el protocolo"""
        url = f"{self.base_url}/mcp"

        # Preparar headers (sin session_id para la primera petición)
        headers = {}
        if self.session_id:
            headers["mcp-session-id"] = self.session_id

        payload = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "weather-mcp-client",
                    "version": "1.0.0"
                }
            }
        }

        with log_status("Inicializando sesión MCP..."):
            response = await self.client.post(url, json=payload, headers=headers)

            # Capturar session_id del servidor
            if not self.session_id and "mcp-session-id" in response.headers:
                self.session_id = response.headers["mcp-session-id"]
                log.info(f"Session ID recibido: {self.session_id}")

            status = response.status_code
            try:
                result = response.json()
            except Exception:
                result = {"error": {"code": status, "message": response.text}}

        if status != 200:
            log.error(f"HTTP {status} al inicializar: {result}")
            return result

        if "error" in result:
            log_json(result["error"], "❌ Error en initialize")
            return result

        log.info("✓ Sesión MCP inicializada correctamente")
        return result

    async def list_tools(self):
        """Lista las herramientas MCP disponibles en el servidor"""
        # Endpoint MCP HTTP montado por el servidor
        url = f"{self.base_url}/mcp"

        # Preparar headers, agregar session_id si ya lo tenemos
        headers = {}
        if self.session_id:
            headers["mcp-session-id"] = self.session_id

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }

        with log_status("Listando herramientas disponibles..."):
            response = await self.client.post(url, json=payload, headers=headers)

            # Capturar session_id del servidor si es la primera petición
            if not self.session_id and "mcp-session-id" in response.headers:
                self.session_id = response.headers["mcp-session-id"]
                log.info(f"Session ID recibido del servidor: {self.session_id}")

            status = response.status_code
            try:
                result = response.json()
            except Exception:
                result = {"error": {"code": status, "message": response.text}}

        if status != 200:
            log.error(f"HTTP {status} al listar herramientas: {result}")
            log.debug(f"Response headers: {dict(response.headers)}")
            return result

        if "error" in result:
            log_json(result["error"], "❌ Error JSON-RPC en tools/list")
            return result

        tools = result.get('result', {}).get('tools', [])

        if tools:
            console.print("\n[bold cyan]🛠️  Herramientas Disponibles:[/bold cyan]")
            for tool in tools:
                console.print(f"  • [green]{tool['name']}[/green]: {tool.get('description','')}")
        else:
            log.warning("No se encontraron herramientas MCP publicadas por el servidor")

        return result

    async def call_tool(self, tool_name: str, arguments: dict = None):
        """Llama a una herramienta MCP publicada por el servidor"""
        # Endpoint MCP HTTP montado por el servidor
        url = f"{self.base_url}/mcp"

        # Preparar headers, agregar session_id si ya lo tenemos
        headers = {}
        if self.session_id:
            headers["mcp-session-id"] = self.session_id

        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }

        with LogContext(f"Herramienta: {tool_name}", "yellow"):
            if arguments:
                log_table("Argumentos", arguments)

            with log_status(f"Ejecutando {tool_name}..."):
                response = await self.client.post(url, json=payload, headers=headers)
                status = response.status_code
                try:
                    result = response.json()
                except Exception:
                    result = {"error": {"code": status, "message": response.text}}

            if status != 200:
                log.error(f"HTTP {status} al ejecutar {tool_name}: {result}")
                log.debug(f"Response headers: {dict(response.headers)}")
                return result

            if 'error' in result:
                log_json(result['error'], "❌ Error JSON-RPC en tools/call")
                return result

            if 'result' in result:
                contents = result['result'].get('content', [])
                if not contents:
                    log.warning("La respuesta no contiene 'content'")
                for content in contents:
                    ctype = content.get('type')
                    if ctype == 'text':
                        log_panel(
                            content.get('text'),
                            title="📝 Resultado (texto)",
                            style="green"
                        )
                    elif ctype == 'json':
                        data = content.get('data') or content.get('json') or {}
                        log_json(data, "🧩 Resultado (JSON)")
                    else:
                        log_panel(str(content), title=f"Resultado ({ctype or 'desconocido'})", style="yellow")

        return result

    # Nota: El servidor actual no expone endpoints de estado/eliminación de sesión.
    # El endpoint HTTP de fastapi-mcp está disponible en /mcp/{session_id}.

    async def close(self):
        """Cierra el cliente"""
        await self.client.aclose()
        log.info("Cliente cerrado correctamente")


async def main():
    """Función de prueba"""

    log_section("PRUEBAS DEL CLIENTE MCP", "bold magenta")

    client = MCPClientHTTP()

    try:
        # 1. Health check (Hello World)
        log_section("1. Health Check", "cyan")
        await client.health_check()

        # 2. Inicializar sesión MCP
        log_section("2. Inicializando Sesión MCP", "cyan")
        await client.initialize()

        # 3. Listar herramientas MCP disponibles
        log_section("3. Listando Herramientas", "cyan")
        await client.list_tools()

        # 4. Llamar a la herramienta de clima expuesta por el servidor
        log_section("4. Obtener clima por ciudad y país", "cyan")
        await client.call_tool("get_weather_by_country", {
            "city": "Caracas",
            "country": "VE"  # Código de país ISO 3166-1 alpha-2
        })

        log_section("PRUEBAS COMPLETADAS ✓", "bold green")

    except Exception as e:
        log.exception(f"Error durante las pruebas: {e}")
        log_section("PRUEBAS FALLIDAS ✗", "bold red")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())