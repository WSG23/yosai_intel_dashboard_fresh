# Machine-Learned Column Mapping

The column mapper can leverage a supervised model to recognize common header variations.
Prepare a CSV file with `header` and `label` columns and train a simple model using scikit-learn:

```python
import joblib
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

training = pd.read_csv('training_data.csv')
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(training['header'])
clf = MultinomialNB()
clf.fit(X, training['label'])
joblib.dump(clf, 'data/column_model.joblib')
joblib.dump(vectorizer, 'data/column_vectorizer.joblib')
```

These files will be loaded by `ColumnMappingService` when `learning_enabled` is enabled in the configuration.

Sample training logs used for testing can be found in `docs/example_data/training/`.
