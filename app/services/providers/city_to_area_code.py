"""US city to area code mapping.

Used by the provider router to translate a city name into TextVerified
area code preferences. TextVerified's proximity chain handles the rest.

lookup(city) -> List[str]  (empty list if city unknown — graceful, not an error)
"""

from typing import List

_CITY_MAP = {
    "new york": ["212", "646", "718", "917", "929"],
    "los angeles": ["213", "310", "323", "424", "747", "818"],
    "chicago": ["312", "773", "872"],
    "houston": ["281", "346", "713", "832"],
    "phoenix": ["480", "602", "623"],
    "philadelphia": ["215", "267", "445"],
    "san antonio": ["210", "726"],
    "san diego": ["619", "858"],
    "dallas": ["214", "469", "972"],
    "san jose": ["408", "669"],
    "austin": ["512", "737"],
    "jacksonville": ["904"],
    "fort worth": ["682", "817"],
    "columbus": ["380", "614"],
    "charlotte": ["704", "980"],
    "indianapolis": ["317"],
    "san francisco": ["415", "628"],
    "seattle": ["206", "253", "360"],
    "denver": ["303", "720"],
    "nashville": ["615", "629"],
    "oklahoma city": ["405"],
    "el paso": ["915"],
    "washington dc": ["202"],
    "washington": ["202"],
    "las vegas": ["702", "725"],
    "louisville": ["502"],
    "memphis": ["901"],
    "portland": ["503", "971"],
    "baltimore": ["410", "443", "667"],
    "milwaukee": ["262", "414"],
    "albuquerque": ["505"],
    "tucson": ["520"],
    "fresno": ["559"],
    "sacramento": ["279", "916"],
    "mesa": ["480"],
    "kansas city": ["816"],
    "atlanta": ["404", "470", "678", "770"],
    "omaha": ["402"],
    "colorado springs": ["719"],
    "raleigh": ["919", "984"],
    "long beach": ["562"],
    "virginia beach": ["757"],
    "minneapolis": ["612", "763", "952"],
    "tampa": ["813"],
    "new orleans": ["504"],
    "arlington": ["682", "817"],
    "wichita": ["316"],
    "bakersfield": ["661"],
    "aurora": ["303", "720"],
    "anaheim": ["714"],
    "miami": ["305", "786"],
    "boston": ["339", "617", "857"],
    "detroit": ["313"],
    "cleveland": ["216"],
    "pittsburgh": ["412"],
    "cincinnati": ["513"],
    "st louis": ["314"],
    "saint louis": ["314"],
    "orlando": ["321", "407", "689"],
    "salt lake city": ["385", "801"],
    "richmond": ["804"],
    "buffalo": ["716"],
    "hartford": ["860"],
    "new haven": ["203"],
    "bridgeport": ["203"],
}


def lookup(city: str) -> List[str]:
    """Return area codes for a US city name.

    Case-insensitive. Returns empty list if city is unknown — caller
    should treat this as graceful (no area code filter, not an error).
    """
    if not city:
        return []
    return _CITY_MAP.get(city.strip().lower(), [])
