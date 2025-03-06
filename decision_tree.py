import dataclasses
import itertools
import math

from collections import Counter
from typing import ClassVar, Callable, Any

import pandas as pd

def population_to_percentages(pop_list : list) -> list[float]:
    if not pop_list:
        return []
    c = Counter(pop_list)
    c_sum = sum(c.values())
    return [v / c_sum for v in c.values()]

def pop_max(pop_list : list) -> float:
    pop_list = list(pop_list)
    if not pop_list:
        return 1.0
    c = Counter(pop_list)
    c_sum = sum(c.values())
    return max([n for n in c.values()]) / c_sum

def pop_entropy(prob_list : list) -> float:
    if not prob_list:
        return 0.0
    return -sum([p * math.log2(p) for p in prob_list])

def condition2str(feature : str, condition : bool, value : Any) -> str:
    if isinstance(value, bool):
        return ("" if condition == value else "!") + feature
    return f'{feature}{"==" if condition else "!="}{str(value)}'

@dataclasses.dataclass
class FeatureDecisionTree:
    feature : str
    value : str
    children : dict[bool, 'FeatureDecisionTree'] = dataclasses.field(default_factory=dict)
    outcome_probabilities : dict[Any, float] = None
    depth : int = 0
    score : float = None

    def is_leaf(self) -> bool:
        return self.feature is None
    def __getitem__(self, item):
        return self.children[item]
    def __str__(self):
        if self.value is None:
            return str(self.outcome_probabilities)
        if self.value is True:
            return f'{self.feature}, {str(self.outcome_probabilities)}'
        return f'{self.feature}=={str(self.value)}, {str(self.outcome_probabilities)}'

    def __repr__(self):
        return str(self)

    @staticmethod
    def from_dataset(df : pd.DataFrame, outcome_column : str, population_metric : Callable[[list], float] = None,
                     **kwargs) \
            -> 'FeatureDecisionTree':
        depth = kwargs.get('depth') if kwargs.get('depth') else 0
        max_depth = kwargs.get('max_depth')
        if population_metric is None:
            population_metric = pop_entropy

        if outcome_column not in df.columns:
            raise Exception('Outcomes column "%s" not in dataframe' % outcome_column)
        feature_dict = {k:set(df[k]) for k in df.columns if k != outcome_column}
        y_population = Counter(df[outcome_column])
        y_sum = sum(y_population.values())
        y_probabilities = {k:v/y_sum for k,v in y_population.items()}
        current_score = population_metric(y_probabilities.values())
        node = FeatureDecisionTree(feature=None, value=None, outcome_probabilities=y_probabilities,
                                   depth=depth, score=current_score)
        if max_depth is not None and depth >= max_depth:
            return node
        # find feature by which to split
        best_score = current_score
        best_feature, best_value = None, None
        best_df_true, best_df_false = None, None
        for feature in feature_dict:
            if len(feature_dict[feature]) < 2:
                continue
            for value in feature_dict[feature]:
                df_true, df_false = df[df[feature]==value], df[~(df[feature]==value)]
                distributions = [population_to_percentages(split_df[outcome_column].to_list())
                                 for split_df in (df_true, df_false)]
                score = sum([population_metric(d) for d in distributions]) / 2
                if score < best_score:
                    best_score = score
                    best_feature, best_value = feature, value
                    best_df_true, best_df_false = df_true, df_false
        if best_score < current_score: # we have a split
            node.feature, node.value = best_feature, best_value
            if isinstance(node.value, bool) and node.value is False: # none of this A==False stuff
                node.value = True
                best_df_true, best_df_false = best_df_false, best_df_true
            for k, _df in zip((True, False), (best_df_true, best_df_false)):
                node.children[k] = FeatureDecisionTree.from_dataset(_df, outcome_column,
                                        population_metric, depth=depth+1, max_depth=max_depth)

        return node

    def find_outcome(self, features_dict : dict[str, Any]) -> dict[str, float]:
        node = self
        while not node.is_leaf() and node.feature in features_dict:
            node = node[features_dict[node.feature] == node.value]
        return node.outcome_probabilities

    def get_outcomes(self) -> list[tuple[dict[Any, float], list[tuple[str, bool, Any]]]]:
        if self.is_leaf():
            return [(self.outcome_probabilities, [])]
        outcomes = []
        for condition in (False, True):
            for population, outcome_list in self.children[condition].get_outcomes():
                outcome_list = [(self.feature, condition, self.value)] + outcome_list
                outcomes.append((population, outcome_list))
        return outcomes

class FeatureDecisionTreeClassifier:
    OUTCOMES = '*OUTCOMES*'
    def __init__(self):
        self.tree : FeatureDecisionTree = None
        self.features : list[str] = None
        self.outcomes : list = None

    def fit(self, X : pd.DataFrame|list[list], y : list, **kwargs) -> 'FeatureDecisionTreeClassifier':
        features = kwargs.get('features')
        max_depth = kwargs.get('max_depth')
        population_metric = kwargs.get('population_metric')
        if len(X) != len(y):
            raise Exception('Length of X not equal to length of y.')
        if isinstance(X, pd.DataFrame):
            if not features:
                features = list(X.columns)
            else:
                cols = list(X.columns)
                if len(cols) != len(features):
                    raise Exception('Length of features not equal to length of columns')
                X = X.rename(columns={k:v for k,v in zip(cols, features)})
        else: # not dataframe
            if len({len(row) for row in X}) != 1:
                raise Exception('Multiple row lengths.')
            if not features:
                features = [f'x{i}' for i in range(len(X[0]))]
            elif len(features) != len(X[0]):
                raise Exception('Length of features not equal to length of columns')
            X = pd.DataFrame(X, columns=features)
        if None in features:
            raise Exception('Features cannot contain None')
        if FeatureDecisionTreeClassifier.OUTCOMES in features:
            raise Exception('Features cannot contain ' + FeatureDecisionTreeClassifier.OUTCOMES)
        self.features = features
        df = pd.DataFrame(X)
        df[FeatureDecisionTreeClassifier.OUTCOMES] = y
        self.tree = FeatureDecisionTree.from_dataset(df, FeatureDecisionTreeClassifier.OUTCOMES,
                                                     population_metric, max_depth=max_depth)
        self.outcomes = list(set(y))
        return self

    def predict_population(self, X : pd.DataFrame|list[list]) -> list[dict[str, float]]:
        if not self.tree:
            raise Exception('Model not fitted.')
        if not isinstance(X, pd.DataFrame):
            if len({len(row) for row in X}) != 1:
                raise Exception('Multiple row lengths.')
            if len(X[0]) != len(self.features):
                raise Exception('Number of columns not equal to number of features')
            X = pd.DataFrame(X, columns=self.features)
        results = list(X.apply(lambda r : self.tree.find_outcome(r), axis=1))
        return results

    def predict_proba(self, X : pd.DataFrame|list[list]) -> list[list[float]]:
        results = self.predict_population(X)
        results = [[d[k] if k in d else 0.0 for k in self.outcomes] for d in results]
        return results

    def predict(self, X : pd.DataFrame|list[list]) -> list:
        probs = self.predict_population(X)
        # get feature with highest probability
        probs = [list(d.items()) for d in probs]
        for d in probs:
            d.sort(key=lambda t : -t[1]) # highest first
        return [t[0][0] for t in probs]

    def score(self, X : pd.DataFrame|list[list], y : list) -> float:
        predictions = self.predict(X)
        if len(y) != len(predictions):
            raise Exception('Length of predictions and length of actual outcomes not equal.')
        results = [pred==actual for pred, actual in zip(predictions, y)]
        return sum(results) / len(results)

if __name__ == "__main__":
    df = pd.DataFrame(list(itertools.product(*([(False,True)]*3))), columns=list('ABC'))
    df['f'] = df.apply(lambda r: '1' if ((r['A'] or r['B']) and not r['C']) else '0', axis=1)
    tree = FeatureDecisionTree.from_dataset(df, 'f')

    outcomes = tree.get_outcomes()
    for o in outcomes:
        print(o[0], [condition2str(*i) for i in o[1]])

    dt = FeatureDecisionTreeClassifier()
    dt.fit(df[['A', 'B', 'C']], df['f'])
    print(dt.predict_population([[True, True, True]]))
    print(dt.predict_proba([[True, True, True]]))
    print(dt.predict([[True, True, True]]))
