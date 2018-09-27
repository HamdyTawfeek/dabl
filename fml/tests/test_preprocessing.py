from fml.preprocessing import (detect_types_dataframe, FriendlyPreprocessor,
                               DirtyFloatCleaner)
import pandas as pd
import numpy as np
from sklearn.datasets import load_iris

X_cat = pd.DataFrame({'a': ['b', 'c', 'b'],
                      'second': ['word', 'no', '']})


def make_dirty_float():
    rng = np.random.RandomState(0)
    cont_clean = ["{:2.2f}".format(x) for x in rng.uniform(size=100)]
    dirty = pd.DataFrame(cont_clean)
    dirty[::12] = "missing"
    dirty.iloc[3, 0] = "garbage"
    return dirty


def test_detect_types_dataframe():
    res = detect_types_dataframe(X_cat)
    assert len(res) == 2
    assert res.categorical.all()
    assert ~res.continuous.any()

    iris = load_iris()
    res_iris = detect_types_dataframe(pd.DataFrame(iris.data))
    assert (res_iris.sum(axis=1) == 1).all()
    assert res_iris.continuous.sum() == 4


def test_detect_string_floats():
    # test if we can find floats that are encoded as strings
    # sometimes they have weird missing values
    rng = np.random.RandomState(0)
    cont_clean = ["{:2.2f}".format(x) for x in rng.uniform(size=100)]
    dirty = pd.Series(cont_clean)
    # FIXME hardcoded frequency of tolerated missing
    # FIXME add test with integers
    # FIXME whitespace?
    dirty[::12] = "missing"
    # only dirty:
    res = detect_types_dataframe(pd.DataFrame(dirty))
    assert len(res) == 1
    assert res.dirty_float[0]

    # dirty and clean
    X = pd.DataFrame({'a': cont_clean, 'b': dirty})
    res = detect_types_dataframe(X)
    assert len(res) == 2
    assert res.continuous['a']
    assert ~res.continuous['b']
    assert ~res.dirty_float['a']
    assert res.dirty_float['b']


def test_transform_dirty_float():
    dirty = make_dirty_float()
    dfc = DirtyFloatCleaner()
    dfc.fit(dirty)
    res = dfc.transform(dirty)
    # TODO test for new values in test etc
    assert res.shape == (100, 3)
    assert (res.dtypes == float).all()
    assert res.x0_missing.sum() == 9
    assert res.x0_garbage.sum() == 1


def test_simple_preprocessor():
    sp = FriendlyPreprocessor()
    sp.fit(X_cat)
    trans = sp.transform(X_cat)
    assert trans.shape == (3, 5)

    iris = load_iris()
    sp = FriendlyPreprocessor()
    sp.fit(iris.data)


def test_simple_preprocessor_dirty_float():
    dirty = pd.DataFrame(make_dirty_float())
    fp = FriendlyPreprocessor()
    fp.fit(dirty)
    res = fp.transform(dirty)
    assert res.shape == (100, 3)
    rowsum = res.sum(axis=0)
    # count of "garbage"
    assert rowsum[1] == 1
    # count of "missing"
    assert rowsum[2] == 9

    # make sure we can transform a clean column
    fp.transform(pd.DataFrame(['0', '1', '2']))


# TODO add tests that floats as strings are correctly interpreted
# TODO add test that weird missing values in strings are correctly interpreted
# TODO check that we detect ID columns
# TODO test for weirdly indexed dataframes
# TODO test select cont
# TODO test non-trivial case of FriendlyPreprocessor?!"!"