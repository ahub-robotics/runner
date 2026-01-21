# -*- coding: utf-8 -*-
"""
Version Info for Windows Executable
====================================
Este archivo define los metadatos que aparecerán en las propiedades del .exe
Se usa con PyInstaller para agregar información profesional al ejecutable.

Uso en .spec file:
    EXE(..., version='branding/version_info.py', ...)
"""

import json
from pathlib import Path

# Cargar metadatos
metadata_file = Path(__file__).parent / 'app_metadata.json'
with open(metadata_file, 'r', encoding='utf-8') as f:
    metadata = json.load(f)

win_meta = metadata['windows']
version = metadata['version']

# Convertir versión a formato Windows (4 números)
version_parts = version.split('.')
while len(version_parts) < 4:
    version_parts.append('0')
version_tuple = tuple(map(int, version_parts))

# ==============================================================================
# VERSION INFORMATION (Windows Resource File Format)
# ==============================================================================

VSVersionInfo(
    ffi=FixedFileInfo(
        # filevers y prodvers deben ser tuplas de 4 enteros (major, minor, patch, build)
        filevers=version_tuple,
        prodvers=version_tuple,

        # Máscara de bits - define qué campos son válidos
        mask=0x3f,

        # Flags de bits
        flags=0x0,

        # Sistema operativo
        OS=0x40004,  # VOS_NT_WINDOWS32

        # Tipo de archivo
        fileType=0x1,  # VFT_APP (application)

        # Subtipo de archivo
        subtype=0x0,  # VFT2_UNKNOWN

        # Fecha del archivo (no usado)
        date=(0, 0)
    ),

    kids=[
        StringFileInfo(
            [
                StringTable(
                    '040904B0',  # English (US), Unicode
                    [
                        StringStruct('CompanyName', win_meta['company_name']),
                        StringStruct('FileDescription', win_meta['file_description']),
                        StringStruct('FileVersion', win_meta['file_version']),
                        StringStruct('InternalName', win_meta['internal_name']),
                        StringStruct('LegalCopyright', win_meta['legal_copyright']),
                        StringStruct('OriginalFilename', win_meta['original_filename']),
                        StringStruct('ProductName', win_meta['product_name']),
                        StringStruct('ProductVersion', win_meta['product_version']),
                        StringStruct('Comments', win_meta['comments']),
                        StringStruct('LegalTrademarks', win_meta['trademark']),
                    ]
                )
            ]
        ),
        VarFileInfo([VarStruct('Translation', [1033, 1200])])  # English, Unicode
    ]
)