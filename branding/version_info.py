# -*- coding: utf-8 -*-
# UTF-8
#
# Version Info for Windows Executable
# ====================================
# Este archivo define los metadatos que aparecerán en las propiedades del .exe
# Se usa con PyInstaller para agregar información profesional al ejecutable.
#
# IMPORTANTE: Este archivo NO debe contener imports ni código ejecutable.
# PyInstaller lo evalúa directamente como una estructura de datos.

VSVersionInfo(
    ffi=FixedFileInfo(
        # filevers y prodvers deben ser tuplas de 4 enteros (major, minor, patch, build)
        filevers=(1, 0, 0, 0),
        prodvers=(1, 0, 0, 0),
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
                        StringStruct('CompanyName', 'AHUB Robotics'),
                        StringStruct('FileDescription', 'Robot Runner - Remote Automation System'),
                        StringStruct('FileVersion', '1.0.0.0'),
                        StringStruct('InternalName', 'RobotRunner'),
                        StringStruct('LegalCopyright', 'Copyright © 2026 AHUB Robotics'),
                        StringStruct('OriginalFilename', 'RobotRunner.exe'),
                        StringStruct('ProductName', 'Robot Runner'),
                        StringStruct('ProductVersion', '1.0.0.0'),
                        StringStruct('Comments', 'Professional automation deployment platform'),
                        StringStruct('LegalTrademarks', 'Robot Runner™'),
                    ]
                )
            ]
        ),
        VarFileInfo([VarStruct('Translation', [1033, 1200])])  # English, Unicode
    ]
)