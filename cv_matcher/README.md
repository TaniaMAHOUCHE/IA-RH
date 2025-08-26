Installation & lancement
git clone https://github.com/ton-repo/cv_matcher.git
cd cv_matcher
pip install -r requirements.txt
streamlit run app.py

Structure du projet
cv-matcher/
│── app.py                 
│── config.py              
│── requirements.txt      
│── services/
│   ├── translation.py     
│   ├── extraction.py    
│   ├── matching.py       
│   ├── storage.py         
│── static/
│   └── style.css          
