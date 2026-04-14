# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    [r'F:\AI_CODING\JMU_nauticalEnglishOralAndListening\src\main.py'],
    pathex=[r'F:\AI_CODING\JMU_nauticalEnglishOralAndListening\src'],
    binaries=[],
    datas=[('F:\\AI_CODING\\JMU_nauticalEnglishOralAndListening\\src\\nautical_english\\ui\\resources', 'nautical_english/ui/resources'), ('F:\\AI_CODING\\JMU_nauticalEnglishOralAndListening\\corpus\\db', 'corpus/db'), ('F:\\AI_CODING\\JMU_nauticalEnglishOralAndListening\\SMCP_DATA\\audioFile', 'SMCP_DATA/audioFile'), ('F:\\AI_CODING\\JMU_nauticalEnglishOralAndListening\\assets', 'assets')],
    hiddenimports=[
        'nautical_english',
        'nautical_english.asr',
        'nautical_english.tts',
        'nautical_english.nlp',
        'nautical_english.corpus',
        'nautical_english.feedback',
        'nautical_english.training',
        'nautical_english.ui',
        'sounddevice',
        'soundfile',
        'faster_whisper',
        'sentence_transformers',
        'sqlalchemy.dialects.sqlite',
    ],
    hookspath=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='maritime_english_trainer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=r'F:\AI_CODING\JMU_nauticalEnglishOralAndListening\assets\icons\app.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='maritime_english_trainer',
)
