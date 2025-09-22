# tests/intercorrencias/test_spectacular_ext.py
import intercorrencias.spectacular_ext as ext

def test_remotejwt_scheme_definition_unitario():
    # Jeito 1: passar target "dummy"
    scheme = ext.RemoteJWTAuthScheme(target=None)
    definition = scheme.get_security_definition(auto_schema=None)
    assert definition == {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }

    # --- OU ---

    # Jeito 2: burlar o __init__ (não precisa do target)
    s2 = object.__new__(ext.RemoteJWTAuthScheme)  # não chama __init__
    definition2 = s2.get_security_definition(auto_schema=None)
    assert definition2["scheme"] == "bearer"
    assert definition2["type"] == "http"
    assert definition2.get("bearerFormat") == "JWT" 
