import requests
import re

def obtener_pictograma_arasaac(palabra, idioma="es"):
    """
    Obtiene el pictograma de ARASAAC para una palabra específica

    Args:
        palabra (str): La palabra para buscar su pictograma
        idioma (str): Código del idioma (por defecto 'es' para español)

    Returns:
        str: URL de la imagen del pictograma o None si no se encuentra
    """
    base_url = "https://api.arasaac.org/api/pictograms"
    search_endpoint = f"{base_url}/{idioma}/search/{palabra}"

    try:
        response = requests.get(search_endpoint)

        # Verifica status y contenido no vacío
        if response.status_code == 200 and response.content:
            pictogramas = response.json()
            if pictogramas and len(pictogramas) > 0:
                pictograma_id = pictogramas[0]["_id"]

                # Intenta PNG
                url_png = f"https://static.arasaac.org/pictograms/{pictograma_id}/{pictograma_id}_500.png"
                if requests.head(url_png).status_code == 200:
                    return url_png

                # Intenta SVG
                url_svg = f"https://static.arasaac.org/pictograms/{pictograma_id}/{pictograma_id}.svg"
                if requests.head(url_svg).status_code == 200:
                    return url_svg

        print(f"No se encontró pictograma para '{palabra}' (status: {response.status_code})")
        return None

    except Exception as e:
        print(f"Error al buscar el pictograma para '{palabra}': {str(e)}")
        return None


# Esta función ya no es necesaria en la versión simplificada


def obtener_todos_pictogramas(idioma="es"):
    """
    Obtiene todos los pictogramas de la API de ARASAAC
    Args:
        idioma = idioma de los pictos
    Returns:
        Objeto JSON con todos los pictos
    """
    base_url = "https://api.arasaac.org/api/pictograms"
    search_endpoint = f"{base_url}/all/{idioma}"
    try:
        response = requests.get(search_endpoint)
        if response.status_code == 200 and response.content:
            pictos = response.json()
            if pictos and len(pictos) > 0:
                return pictos
            else:
                return None
        else:
            return None
    except Exception as e:
        print(f"Error al conseguir todos los pictogramas': {str(e)}")
        return None

def texto_a_pictogramas_arasaac(frase):
    """
    Convierte una frase de texto en pictogramas de ARASAAC

    Args:
        frase (str): La frase a convertir

    Returns:
        list: Lista de tuplas (palabra, url_pictograma)
    """
    # Convertir la frase a minúsculas
    frase = frase.lower()

    # Dividir la frase en palabras (excluyendo signos de puntuación)
    palabras = re.findall(r'\b\w+\b', frase)

    resultados = []

    # Para cada palabra, buscar su pictograma
    for palabra in palabras:
        # Ignorar palabras muy cortas (artículos, etc.)
        if len(palabra) <= 1:
            resultados.append((palabra, None))
            continue

        url_pictograma = obtener_pictograma_arasaac(palabra)
        resultados.append((palabra, url_pictograma))

    return resultados

def obtener_pictogramas_por_categoria(categoria, idioma="es"):
    """
    Obtiene todos los pictogramas de una categoría de ARASAAC.

    Returns:
        pictos_categorizados = Lista de tuplas (Palabra. URL)
    """
    pictos = obtener_todos_pictogramas()
    pictos_categorizados = []
    categoria_set = set(categoria)
    for item in pictos:
        cats_en_comun = categoria_set & set(item.get("categories",[]))
        if cats_en_comun:
            keywords = item.get("keywords", [])
            if keywords:
                primera_keyword = keywords[0].get("keyword")
                url_png = f"https://static.arasaac.org/pictograms/{item['_id']}/{item['_id']}_500.png"
                pictos_categorizados.append((primera_keyword, url_png))
            else:
                print("ERROR: No se ha podido acceder a las Keywords de los pictogramas")

    if pictos_categorizados:
        return pictos_categorizados
    else:
        print("ERROR: No se ha encontrado pictos de la categoría escogida")
        return None