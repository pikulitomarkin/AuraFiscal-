# RoboFiscal — Matheus Costa NFS-e

Emissão de NFS-e Nacional (Sefin) para **MATHEUS COSTA SERVICOS MEDICOS LTDA** (Tubarão-SC), com dois canais no mesmo app:

| Canal | Descrição na nota |
|--------|-------------------|
| **ClickCannabis** | `Ref. a consulta pela clickcannabis` |
| **Bliss** | `Ref. a consulta pela bliss` |

## Comportamento

- **Valor**: prioridade do PDF/relatório; fallback configurável na UI
- **Hash do paciente**: vai nas **observações** da NFS-e (`xDescServ` + discriminação)
- **Serviço**: LC 116 `04.01.01` + NBS `1.2301.21.00`
- **Município**: Tubarão-SC (`4218707`), série DPS `70000`, IM `89944`
- **Regime**: Optante Simples Nacional (ME/EPP)

## Certificado

Configure no Railway (ou local):

```bash
CERTIFICATE_CERT_PEM=<base64 do cert.pem>
CERTIFICATE_KEY_PEM=<base64 do key.pem>
```

Ou coloque `certificados/cert.pem` e `certificados/key.pem`.

## Subir

```bash
pip install -r requirements.txt
cp .env.example .env   # ajuste se necessário
streamlit run app_nfse_enhanced.py
```

Login padrão: `admin` / `admin` (troque em produção).

## Estrutura herdada

Baseado no emissor Sefin com certificado digital (sem IPM). Configs do cliente em `config/client.py` e `config/settings.py`.
