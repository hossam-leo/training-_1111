import importlib.util, shutil
mods=['fastapi','pydantic','yaml','pytest']
print('ProctorStream environment validation')
for m in mods: print(f"{m}: {'ok' if importlib.util.find_spec(m) else 'missing'}")
print(f"docker: {'ok' if shutil.which('docker') else 'not installed (optional)'}")
