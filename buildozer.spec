[app]
title = BlackFoxy AI
package.name = blackfoxyai
package.domain = org.blackfoxy

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 1.0

requirements = python3,kivy,kivymd,pyttsx3

orientation = portrait
fullscreen = 0

android.permissions = INTERNET, RECORD_AUDIO

android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
