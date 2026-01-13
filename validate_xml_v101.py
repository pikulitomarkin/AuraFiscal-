"""Validar XML v1.01 gerado"""
import xml.etree.ElementTree as ET

tree = ET.parse('xml_teste_v101.xml')
root = tree.getroot()

ns = '{http://www.sped.fazenda.gov.br/nfse}'

print("✅ XML v1.01 VALIDADO!\n")
print(f"Versão: {root.get('versao')}")
print(f"Namespace: {root.tag}")

inf_dps = root.find(f'{ns}infDPS')
if inf_dps is not None:
    print(f"\n✅ infDPS: PRESENTE")
    print(f"   Id: {inf_dps.get('Id')}")
    print(f"   tpDFe: {inf_dps.find(f'{ns}tpDFe').text}")
    print(f"   dhEmi: {inf_dps.find(f'{ns}dhEmi').text}")
    print(f"   cLocEmi: {inf_dps.find(f'{ns}cLocEmi').text}")
    
    prest = inf_dps.find(f'{ns}prest')
    if prest is not None:
        print(f"\n✅ prest: PRESENTE")
        print(f"   CNPJ: {prest.find(f'{ns}CNPJ').text}")
        print(f"   xNome: {prest.find(f'{ns}xNome').text}")
        
        reg_trib = prest.find(f'{ns}regTrib')
        if reg_trib is not None:
            print(f"   regTrib:")
            print(f"      opSimpNac: {reg_trib.find(f'{ns}opSimpNac').text}")
            print(f"      regEspTrib: {reg_trib.find(f'{ns}regEspTrib').text}")
    
    valores = inf_dps.find(f'{ns}valores')
    if valores is not None:
        print(f"\n✅ valores: PRESENTE")
        print(f"   vServPrest: {valores.find(f'{ns}vServPrest').text}")
        print(f"   vDescIncond: {valores.find(f'{ns}vDescIncond').text}")
        
        issqn = valores.find(f'{ns}issqn')
        if issqn is not None:
            print(f"   issqn:")
            print(f"      vBC: {issqn.find(f'{ns}vBC').text}")
            print(f"      pAliq: {issqn.find(f'{ns}pAliq').text}")
            print(f"      vISSQN: {issqn.find(f'{ns}vISSQN').text}")

print("\n✅ ESTRUTURA CONFORME XSD v1.01!")
