import inspect
import Website.settings as s
print('settings file:', inspect.getsourcefile(s))
print('INSTALLED_APPS:', s.INSTALLED_APPS)
print("'devloom' in INSTALLED_APPS:", 'devloom' in s.INSTALLED_APPS)
print("devloom literal in source?", "'devloom'" in inspect.getsource(s))
print('\n=== source (first 200 chars) ===')
src = inspect.getsource(s)
print(src[:200])
