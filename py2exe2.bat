pyinstaller --name=RA
    --onefile 
    --hidden-import=sklearn \
    --hidden-import=sklearn.pipeline \
    --hidden-import=sklearn.utils._weight_vector \
    --hidden-import=sklearn.neighbors.typedefs \
    --hidden-import=sklearn.tree._utils \
    --hidden-import=sklearn.ensemble._hist_gradient_boosting.common \

    --hidden-import=sklearn.metrics._pairwise_distances_reduction._datasets_pair 
    --hidden-import=sklearn.metrics._pairwise_distances_reduction._middle_term_computer
   
 CCHPM.py




pyinstaller --name=RATool --onefile --hidden-import=sklearn --hidden-import=sklearn.pipeline --hidden-import=sklearn.utils._weight_vector --hidden-import=sklearn.neighbors.typedefs --hidden-import=sklearn.feature_extraction --hidden-import=sklearn.metrics  --hidden-import=sklearn.tree._utils  --hidden-import=sklearn.ensemble._hist_gradient_boosting.common --hidden-import=sklearn.metrics._pairwise_distances_reduction._datasets_pair     --hidden-import=sklearn.metrics._pairwise_distances_reduction._middle_term_computer --hidden-import=fuzzywuzzy --add-data="raiders.txt;." --add-data="classifier.joblib;." -F -w CCHPM.py -i CCHPM.ico -n  "CCHPM v3.01"

pyinstaller -F -w CCHPM.py -i CCHPM.ico -n  "CCHPM v3.01"


pyinstaller --name=CCHPM --onefile --hidden-import=sklearn --hidden-import=sklearn.pipeline --hidden-import=sklearn.utils._weight_vector --hidden-import=sklearn.neighbors.typedefs --hidden-import=sklearn.feature_extraction --hidden-import=sklearn.metrics  --hidden-import=sklearn.tree._utils  --hidden-import=sklearn.ensemble._hist_gradient_boosting.common --hidden-import=sklearn.metrics._pairwise_distances_reduction._datasets_pair     --hidden-import=sklearn.metrics._pairwise_distances_reduction._middle_term_computer --hidden-import=fuzzywuzzy -F -w CCHPM.py -i CCHPM.ico -n  "CCHPM v3.02"
