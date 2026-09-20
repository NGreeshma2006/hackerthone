"""Online speech for languages that are not installed on the user's device."""
import asyncio
import edge_tts

VOICES = {
    'en': 'en-IN-NeerjaNeural', 'hi': 'hi-IN-SwaraNeural',
    'te': 'te-IN-ShrutiNeural', 'ta': 'ta-IN-PallaviNeural',
    'kn': 'kn-IN-SapnaNeural', 'ml': 'ml-IN-SobhanaNeural',
    'mr': 'mr-IN-AarohiNeural', 'bn': 'bn-IN-TanishaaNeural',
}


async def synthesize(text: str, language: str) -> bytes:
    async def collect():
        audio = bytearray()
        async for chunk in edge_tts.Communicate(text, VOICES[language]).stream():
            if chunk['type'] == 'audio':
                audio.extend(chunk['data'])
        if not audio:
            raise RuntimeError('Empty speech response')
        return bytes(audio)
    return await asyncio.wait_for(collect(), timeout=20)
