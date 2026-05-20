import os
import anthropic

_MODELO = "claude-sonnet-4-6"
_MAX_TOKENS = 2048


def generar_plan_stream(prompt_sistema, prompt_usuario):
    """
    Generador que llama a Claude con streaming y hace yield de cada chunk de texto.
    Lanza RuntimeError si la clave API no está configurada o hay error de API.
    """
    clave = os.environ.get("ANTHROPIC_API_KEY", "")
    if not clave:
        raise RuntimeError(
            "ANTHROPIC_API_KEY no está configurada. "
            "Añádela al archivo .env para usar la generación de planes."
        )

    cliente = anthropic.Anthropic(api_key=clave)

    try:
        with cliente.messages.stream(
            model=_MODELO,
            max_tokens=_MAX_TOKENS,
            system=prompt_sistema,
            messages=[{"role": "user", "content": prompt_usuario}],
        ) as stream:
            for chunk in stream.text_stream:
                yield chunk
    except anthropic.AuthenticationError:
        raise RuntimeError("Clave de API inválida. Verifica ANTHROPIC_API_KEY en el archivo .env")
    except anthropic.RateLimitError:
        raise RuntimeError("Límite de uso de la API alcanzado. Inténtalo de nuevo en unos minutos")
    except anthropic.APIError as e:
        raise RuntimeError(f"Error de la API de Claude: {e}")
