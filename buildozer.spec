[app]
title = BlackFoxy AI
package.name = blackfoxyai
package.domain = org.blackfoxy

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,db,txt

version = 1.0

requirements = python3,kivy==2.3.0,kivymd==1.2.0,pillow==10.4.0,sqlite3,plyer,argostranslate

orientation = portrait
fullscreen = 0
android.permissions = INTERNET,RECORD_AUDIO,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
