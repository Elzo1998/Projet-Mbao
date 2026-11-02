"""Indice courant du dossier d'esquisse : une seule ligne à changer pour un nouvel indice (retour client 15/10 : indice D)."""
REV = 'D'
REVISIONS = [('A  13/10/2026  first issue', ''), ('B  15/10/2026  model corrections', ''),
             ('C  15/10/2026  engineer review', ''), ('D  15/10/2026  client review (roof outlets, tiling, canopy)', '')]


def noter(numero, titre, blocs):
    """Retour client 15/10 (indice D) : aucune note de modification sur les planches du dossier client ; les notes et
    finitions de chaque planche sont rangées ici et reprises dans le rapport séparé (rapport_esquisse.py)."""
    import json, os
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'notes'); os.makedirs(d, exist_ok=True)
    json.dump({'planche': numero, 'titre': titre, 'blocs': blocs}, open(os.path.join(d, numero.replace(' ', '') + '.json'), 'w'),
              indent=1, ensure_ascii=False)

# Planches modifiées par l'indice courant : contenu du dossier de contrôle 2D envoyé AVANT tout rendu 3D (porte 2D,
# demande client 15/10 : les rendus ne partent qu'après validation des plans).
MODIFIEES = ['SD-004', 'SD-004A', 'SD-004B', 'SD-005', 'SD-005A', 'SD-005B', 'SD-006', 'SD-006A', 'SD-006B', 'SD-009']
