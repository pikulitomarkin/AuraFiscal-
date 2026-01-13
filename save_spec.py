"""Salvar e analisar spec OpenAPI"""
import httpx
import json

cert_path = r"d:\leitor pdf e geração de notas\certificados\cert.pem"
key_path = r"d:\leitor pdf e geração de notas\certificados\key.pem"

client = httpx.Client(cert=(cert_path, key_path), verify=False)
r = client.get('https://adn.producaorestrita.nfse.gov.br/contribuintes/swagger/v1/swagger.json')
spec = r.json()

with open('api-spec.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(spec, indent=2, ensure_ascii=False))

print("✅ Spec salvo em api-spec.json")
print("\n📍 Endpoints disponíveis:\n")

for path, operations in spec['paths'].items():
    for method, details in operations.items():
        summary = details.get('summary', '')
        print(f"{method.upper():6} {path}")
        if summary:
            print(f"       → {summary}")
        print()
