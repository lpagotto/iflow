# Aqui você PLUGA seu pipeline de processamento
# Entrada: bytes do áudio
# Saída: dict com métricas/valores que alimentarão o PDF

def process_audio_bytes(audio_bytes: bytes) -> dict:
    # TODO: converter para WAV/mono/22kHz, rodar seu modelo, etc.
    # coloque valores fictícios para o MVP:
    return {
        "duracao_s": 18.3,
        "vazao_max_ml_s": 14.2,
        "vazao_media_ml_s": 6.1,
        "volume_total_ml": 265.0,
        "tempo_ate_pico_s": 4.7,
        "classe_dominante": "agua",
    }
