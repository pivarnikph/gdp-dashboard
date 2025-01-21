import json

# Substitua o caminho pelo caminho do arquivo JSON original
with open("/workspaces/gdp-dashboard/credentials.json", "r") as f:
    service_account_data = json.load(f)

# Formate o campo `private_key` corretamente
private_key = service_account_data["private_key"].replace("\n", "\\n")

# Gera a saída para usar no TOML
print(f"""[gcp_service_account]
type = "{service_account_data['type']}"
project_id = "{service_account_data['project_id']}"
private_key_id = "{service_account_data['private_key_id']}"
private_key = "{private_key}"
client_email = "{service_account_data['client_email']}"
client_id = "{service_account_data['client_id']}"
auth_uri = "{service_account_data['auth_uri']}"
token_uri = "{service_account_data['token_uri']}"
auth_provider_x509_cert_url = "{service_account_data['auth_provider_x509_cert_url']}"
client_x509_cert_url = "{service_account_data['client_x509_cert_url']}"
""")
