"""Reproducible sparse linear baselines; training-only learned transformations."""
import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.features.windows import matrix


class LinearBaseline:
    def __init__(self, mode, seed=42):
        if mode not in ('numeric','text','combined'):raise ValueError('Unknown baseline')
        self.mode=mode;self.seed=seed
        self.tfidf=TfidfVectorizer(max_features=10000,ngram_range=(1,2),sublinear_tf=True)
        self.numeric=Pipeline([('imputer',SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True)),
                               ('scale',StandardScaler())])
        self.linear=LogisticRegression(random_state=seed,max_iter=1000,class_weight='balanced')

    def transform(self, rows, fit=False):
        blocks=[]
        if self.mode in ('numeric','combined'):
            x=np.asarray(matrix(rows),dtype=float)
            blocks.append(csr_matrix(self.numeric.fit_transform(x) if fit else self.numeric.transform(x)))
        if self.mode in ('text','combined'):
            texts=[w['text'] for w in rows]
            blocks.append(self.tfidf.fit_transform(texts) if fit else self.tfidf.transform(texts))
        return hstack(blocks,format='csr') if len(blocks)>1 else blocks[0]

    def fit(self, rows):
        self.fit_rows=len(rows)
        self.linear.fit(self.transform(rows,fit=True),[w['label'] for w in rows])
        if np.any(self.linear.n_iter_>=self.linear.max_iter):raise RuntimeError('Linear baseline did not converge')
        return self

    def scores(self, rows):return self.linear.decision_function(self.transform(rows))
