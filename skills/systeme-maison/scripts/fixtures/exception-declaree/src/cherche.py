MOTIFS = ['Permission is hereby granted']


def contient_notice(texte):
    return any(m in texte for m in MOTIFS)
