'''
Assistant de selection automatique du bon test statistique.
Pose les bonnes questions et recommande le test adapte.
'''


def selectionner_test(
    type_variable: str,
    nb_groupes: int = 2,
    apparie: bool = False,
    normal: bool = True,
) -> dict:
    '''
    Recommande le test statistique adapte selon le contexte.

    Parametres :
        type_variable : 'quantitative' | 'qualitative'
        nb_groupes    : nombre de groupes a comparer (1, 2, 3+)
        apparie       : True si mesures repetees sur les memes sujets
        normal        : True si les donnees suivent une loi normale

    Retourne : dict avec le test recommande et les alternatives
    '''
    if type_variable == 'qualitative':
        return {
            'test_recommande': 'chi2',
            'nom': 'Test du Chi2 d independance',
            'condition': 'Tableau de contingence',
            'alternatives': ['Fisher exact (si petits effectifs)'],
        }

    if nb_groupes == 1:
        return {
            'test_recommande': 'shapiro',
            'nom': 'Test de normalite (Shapiro-Wilk)',
            'alternatives': ['Kolmogorov-Smirnov', 'Anderson-Darling'],
        }

    if nb_groupes == 2:
        if normal:
            test = 'ttest_rel' if apparie else 'ttest_ind'
            nom  = 't-test apparie' if apparie else 't-test independant'
            alt  = ['Welch t-test']
        else:
            test = 'wilcoxon' if apparie else 'mann_whitney'
            nom  = 'Wilcoxon' if apparie else 'Mann-Whitney U'
            alt  = []
        return {'test_recommande': test, 'nom': nom, 'alternatives': alt}

    if nb_groupes >= 3:
        if normal:
            return {
                'test_recommande': 'anova',
                'nom':             'ANOVA 1 facteur',
                'post_hoc':        'Tukey HSD',
                'alternatives':    ['Welch ANOVA'],
            }
        else:
            return {
                'test_recommande': 'kruskal',
                'nom':             'Kruskal-Wallis',
                'post_hoc':        'Dunn',
                'alternatives':    [],
            }

    return {'test_recommande': 'inconnu', 'nom': 'Impossible de determiner'}
