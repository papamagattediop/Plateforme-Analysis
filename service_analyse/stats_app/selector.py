def suggest_test(col_x_type, col_y_type, nb_groups=None, normal=None):
    if col_x_type == 'categorical' and col_y_type == 'categorical':
        return {'test_recommande': 'contingence', 'raison': '2 variables categorielles → Chi2 + V de Cramer'}
    if col_x_type == 'numeric' and col_y_type == 'categorical':
        if nb_groups == 2:
            if normal:
                return {'test_recommande': 'ttest', 'raison': '2 groupes + normale → t-test'}
            return {'test_recommande': 'mann_whitney', 'raison': '2 groupes + non normale → Mann-Whitney'}
        if normal:
            return {'test_recommande': 'anova', 'raison': '3+ groupes + normale → ANOVA'}
        return {'test_recommande': 'kruskal', 'raison': '3+ groupes + non normale → Kruskal-Wallis'}
    if col_x_type == 'numeric' and col_y_type == 'numeric':
        return {'test_recommande': 'correlation', 'raison': '2 variables numeriques → correlation + regression'}
    return {'test_recommande': None, 'raison': 'Combinaison non supportee'}