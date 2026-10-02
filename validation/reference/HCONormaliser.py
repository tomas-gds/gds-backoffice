import re

class HCONormaliser:
    DEPT_SCORES = None
    HCO_SCORES = None

    def __init__(self,df,country):
        self.df = df
        self.country = country

    def _best_scored_match(self, parts, score_dict, exclude_keywords=None):
        best_part = ""
        best_score = -1

        for part in parts:
            part_lower = part.lower().strip("-")

            if exclude_keywords and any(k in part_lower for k in exclude_keywords):
                continue

            part_score = max(
                [score for keyword, score in score_dict.items() if keyword in part_lower],
                default=-1
            )

            if part_score > best_score:
                best_score = part_score
                best_part = part

        return best_part if best_score != -1 else ""

    def normalize_hco(self, text):
        import re
        import unicodedata

        text = (text or "").lower()
        text = unicodedata.normalize("NFKC", text)
        text = text.replace("\xa0", " ")
        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        text = text.replace("ae", "ä").replace("oe", "ö").replace("ue", "ü")
        return text.strip()

    def set_HCO_DEPT_SCORES(self):
        if self.country.lower() == "germany":
            self.HCO_SCORES = {
                "rechts der isar": 100,
                "technical university of munich": 100,
                "johannes gutenberg": 100,
                "university medical center": 100,
                "technische universität münchen": 100,
                "philipps university": 100,
                "hamburg eppendorf": 100,
                "hamburg-eppendorf": 100,
                "charit": 100,
                "lmu university hospital": 100,
                "johannes wesling": 100,
                # "tum": 100,
                "tu munich": 100,
                "ludwig-maximilians": 100,
                "ludwigmaximilians": 100,
                "ludwig maximilians": 100,
                "universitätsklinik": 100,
                "universitätsklinikum": 100,

                "hospital": 95,
                "university hospital": 95,
                "krankenhaus": 95,
                "medical center university": 95,
                "medical centeruniversity": 95,
                "clini": 95,
                "klini": 90,
                "hochschule": 90,
                "medical": 90,
                "university of": 90,
                "university medicine": 90,

                "univer": 85,
                "school": 85,
                "ärzte": 85,
                "aerzte": 85,
                "arzt": 85,
                "faculty": 80,
                "zentrum": 75,
                "instit": 70,
                "behring": 70,
                "centre": 65,
                "center": 65,
                "gmbh": 65,
                "research": 50,
                "laboratory": 40,
                "foundation": 30,
                "network": 30,
                "pharma": 30,
                "practice": 30,
                "praxis": 30,
                "siemens": 20,
            }
            self.DEPT_SCORES = {
                "department": 100,
                "dept": 100,
                "division": 90,
                "pneumologie": 80,
                "cardiology": 80,
                "oncology": 80,
                "neurology": 80,
                "chirurgie": 80,
                "radiology": 80,
                "dermatology": 80,
            }

        elif self.country.lower() == "italy":
            self.HCO_SCORES = {
                # --- High-confidence Italian hospitals / institutions ---
                "policlinico": 100,
                "azienda ospedaliera": 100,
                "azienda ospedaliero": 100,
                "azienda ospedaliero universitaria": 100,
                "azienda ospedaliera universitaria": 100,
                "azienda ospedaliera-universitaria": 100,
                "vanvitelli": 100,
                "trust of verona":100,
                "ao": 100,
                "istituto nazionale": 100,
                "istituto tumori": 100,
                "istituto dei tumori": 100,
                "istituto clinico": 100,
                "irccs": 100,  # Scientific Institute for Research, Hospitalization and Healthcare
                "hospital": 100,
                "ospedale": 100,
                "ospedale civile": 100,
                "ospedale universitario": 100,
                "fondazione irccs": 100,
                "humanitas": 100,  # major private hospital network
                "san raffaele": 100,
                "gemelli": 100,  # Policlinico Gemelli
                "careggi": 100,
                "san matteo": 100,
                "sapienza": 100,
                "poliambulanza": 100,
                "aldo moro": 100,
                "bellis": 100,
                "policlinico of bari": 100,
                "giovanni paolo ii": 100,

                "centro ospedaliero": 95,
                "centro medico": 95,
                "struttura sanitaria": 95,
                "unità operativa": 90,
                "reparto": 90,

                # --- Academic / university signals ---
                "università": 85,
                "universita": 85,
                "university": 85,
                "universitario": 85,
                "facoltà": 85,
                "facolta": 85,
                "scuola": 85,

                # --- Generic institution words ---
                "centro": 80,
                "istituto": 80,
                "istituti": 80,
                "dipartimento di medicina": 80,

                # --- Research / pharma ---
                "ricerca": 70,
                "laboratorio": 70,
                "biomed": 70,
                "biotech": 70,
                "farmaceut": 65,

                # --- Corporate / legal entities ---
                "spa": 60,
                "s.p.a": 60,
                "srl": 60,
                "s.r.l": 60,

                # --- Weak signals ---
                "fondazione": 50,
                "network": 40,
                "associazione": 40,
                "studio": 30,
                "medico": 30,
                "ambulatorio": 30,
            }
            self.DEPT_SCORES = {
                "department": 100,
                "dept": 100,
                "division": 90,
                "pneumologie": 80,
                "cardiology": 80,
                "oncology": 80,
                "neurology": 80,
                "chirurgie": 80,
                "radiology": 80,
                "dermatology": 80,
            }

        elif self.country.lower() == "france":
            self.HCO_SCORES = {
                # --- VERY STRONG HOSPITAL SIGNALS ---
                "chu": 100,
                "chru": 100,
                "chuv": 100,
                "aphp": 100,
                "ap hp": 100,
                "assistance publique": 100,
                "hôpitaux": 100,
                "hopitaux": 100,

                # --- STRONG HOSPITAL / CLINIC ---
                "hospital": 95,
                "hôpital": 95,
                "hopital": 95,
                "hospitals": 95,
                "clinique": 95,
                "clinic": 95,

                # --- MEDICAL / INSTITUTION ---
                "centre": 80,
                "center": 80,
                "institut": 75,
                "institute": 75,
                "ghr": 75,
                "ihu": 75,

                # --- UNIVERSITY / RESEARCH ---
                "université": 90,
                "universite": 90,
                "inserm": 85,
                "cnrs": 85,
                "umr": 80,
                "cea": 80,

                # --- SPECIAL CASES ---
                "hospices": 80,
                "foundation": 40,
                "fondation": 40,
                "vision": 60,
                "ophalmologist": 70,
                "ophthalmology center": 80,
                "hia": 85,  # military hospitals

                # --- WEAK / FILTERING SIGNALS ---
                "private office": 20,
                "private practitioner": 20,
            }
            self.DEPT_SCORES = {
                # --- STRUCTURE ---
                "department": 100,
                "dept": 100,
                "service": 95,  # VERY important in France
                "unité": 90,
                "unite": 90,
                "division": 85,

                # --- MEDICAL SPECIALTIES ---
                "cardiology": 80,
                "oncology": 80,
                "neurology": 80,
                "pneumology": 80,
                "pneumologie": 80,
                "chirurgie": 80,
                "surgery": 80,
                "radiology": 80,
                "dermatology": 80,
                "ophthalmology": 80,
            }

        elif self.country.lower() == "switzerland":
            self.HCO_SCORES = {
                # --- Major Swiss institutions / keywords ---
                "universitätsspital zürich": 100,
                "university hospital zurich": 100,
                "usz": 100,

                "universität bern": 100,
                "inselspital": 100,
                "inselspital bern": 100,

                "hôpitaux universitaires de genève": 100,
                "hug": 100,
                "geneva university hospitals": 100,

                "centre hospitalier universitaire vaudois": 100,
                "chuv": 100,
                "lausanne university hospital": 100,

                "universität basel": 100,
                "university hospital basel": 100,

                "eth zurich": 100,
                "epfl": 100,
                "école polytechnique fédérale de lausanne": 100,

                # --- Strong institutional indicators ---
                "universitätsspital": 100,
                "universitätsklinik": 100,
                "universitätsklinikum": 100,
                "university hospital": 100,
                "hôpital universitaire": 100,
                "ospedale universitario": 100,

                # --- Hospitals / clinics ---
                "hospital": 95,
                "spital": 95,
                "hôpital": 95,
                "hopital": 95,
                "ospedale": 95,
                "clinique": 95,
                "klinik": 90,

                # --- Academic ---
                "universität": 90,
                "universite": 90,
                "università": 90,
                "university": 90,
                "hochschule": 90,
                "medical": 90,

                # --- Mid-level indicators ---
                "faculty": 85,
                "faculté": 85,
                "facolta": 85,
                "school": 85,
                "zentrum": 75,
                "centre": 75,
                "centro": 75,
                "institut": 70,
                "institute": 70,
                "research": 50,
                "laboratory": 40,

                # --- Low relevance / private / noise ---
                "foundation": 30,
                "network": 30,
                "pharma": 30,
                "praxis": 30,
                "cabinet": 30,
                "studio": 30,
                "gmbh": 25,
                "ag": 25,
            }

            self.DEPT_SCORES = {
                # --- Core structure ---
                "department": 100,
                "dept": 100,
                "abteilung": 100,
                "service": 100,
                "division": 90,

                # --- Specialties (multilingual) ---
                "pneumologie": 80,
                "pneumology": 80,
                "cardiology": 80,
                "kardiologie": 80,
                "cardiologie": 80,
                "oncology": 80,
                "onkologie": 80,
                "oncologie": 80,
                "neurology": 80,
                "neurologie": 80,
                "chirurgie": 80,
                "surgery": 80,
                "radiology": 80,
                "radiologie": 80,
                "dermatology": 80,
                "dermatologie": 80,
            }

        else:
            self.HCO_SCORES = {
                # --- Strong HCO indicators ---
                "university hospital": 100,
                "academic medical center": 100,
                "medical center": 95,
                "medical centre": 95,
                "hospital": 95,
                "clinic": 90,
                "clinical": 85,

                # --- University / academic ---
                "university": 90,
                "college": 85,
                "school": 85,
                "faculty": 85,
                "academy": 80,

                # --- Research / institute ---
                "institute": 75,
                "institut": 75,
                "centre": 75,
                "center": 75,
                "research": 60,
                "laboratory": 50,
                "lab": 45,

                # --- Healthcare organization terms ---
                "health": 70,
                "healthcare": 70,
                "medical": 70,
                "medicine": 70,
                "care": 60,
                "foundation": 40,
                "network": 35,

                # --- Private practice / companies / weaker HCO signals ---
                "practice": 35,
                "praxis": 35,
                "group": 30,
                "pharma": 25,
                "pharmaceutical": 25,
                "biotech": 25,
                "gmbh": 20,
                "ltd": 20,
                "limited": 20,
                "inc": 20,
                "corp": 20,
                "corporation": 20,
                "company": 20,
            }

            self.DEPT_SCORES = {
                # --- Generic department indicators ---
                "department": 100,
                "dept": 100,
                "division": 90,
                "unit": 80,
                "section": 75,
                "service": 75,
                "center": 70,
                "centre": 70,
                "program": 60,
                "programme": 60,

                # --- Common specialties ---
                "oncology": 80,
                "hematology": 80,
                "haematology": 80,
                "cardiology": 80,
                "neurology": 80,
                "radiology": 80,
                "dermatology": 80,
                "surgery": 80,
                "internal medicine": 80,
                "pediatrics": 80,
                "paediatrics": 80,
                "pathology": 80,
                "pulmonology": 80,
                "respiratory": 75,
                "gastroenterology": 75,
                "endocrinology": 75,
                "immunology": 75,
                "rheumatology": 75,
            }

    def fix_Italy(self, dept_value, hco_value, city_value):
        hco_norm = self.normalize_hco(hco_value)
        city_value = city_value.lower()

        ans = dept_value, hco_value, city_value

        university_hospital_map = {
            "verona": ("Azienda Ospedaliera Di Verona", "Verona"),
            "pisa": ("Azienda Ospedaliero-Universitaria Pisana", "Pisa"),
            "bari": ("Azienda Osp Policlinico Consorziale", "Bari"),
            "padua": ("Azienda Ospedaliera Di Padova", "Padova"),
            "padova": ("Azienda Ospedaliera Di Padova", "Padova"),
            "ancona": ("A.O.U.Ospedali Riuniti - Ancona", "Ancona"),
            "bologna": ("IRCCS Azienda Ospedaliero - Universitaria di Bologna", "Bologna"),
            "modena": ("Azienda Ospedaliera Policlinico", "Modena"),
            "foggia": ("Azienda Ospedaliero-Universitaria Policlinico Foggia", "Foggia"),
            "cagliari": ("Policlinico Universitario Monserrato Duilio Casula", "Cagliari"),
            "Ferrara": ("Azienda Ospedaliero-Universitaria di Ferrara", "Ferrara"),

        }

        university_hospital_aliases = ["university hospital",
                                       "ospedaliera universitaria","ospedalierauniversitaria",
                                       "ospedaliera universitario","ospedalierauniversitario",
                                       "ospedaliero universitaria","ospedalierouniversitaria",
                                       "ospedaliero universitario","ospedalierouniversitario"]

        if any(alias in hco_norm for alias in university_hospital_aliases):
            city_key = city_value.lower().strip()

            if city_key in university_hospital_map:
                fixed_hco, fixed_city = university_hospital_map[city_key]
                ans = dept_value, fixed_hco, fixed_city
                return ans


        if any(alias in hco_norm for alias in ["hospital trust","riuniti","irccs"]):
            if "verona" in city_value.lower():
                ans = dept_value, "Azienda Ospedaliera Di Verona", "Verona"
                return ans
            elif "terni" in city_value.lower():
                ans = dept_value, "Azienda Ospedaliera S. Maria", "Terni"
                return ans
            elif "ancona" in city_value.lower():
                ans = dept_value, "A.O.U.Ospedali Riuniti - Ancona", "Ancona"
                return ans
            elif "bologna" in city_value.lower():
                ans = dept_value, "IRCCS Azienda Ospedaliero - Universitaria di Bologna", "Bologna"
                return ans
            elif "palermo" in city_value.lower():
                ans = dept_value, "IRCCS ISMETT – UPMC", "Parlemo"
                return ans
            elif "foggia" in city_value.lower():
                ans = dept_value, "Azienda Ospedaliero-Universitaria Policlinico Foggia", "Foggia"
                return ans
            elif "pavia" in city_value.lower():
                if "maugeri" in hco_norm:
                    ans = dept_value, "Istituti Clinici Scientifici Maugeri IRCCS", "Pavia"
                else:
                    ans = dept_value, "Ospedale Policlinico San Matteo", "Pavia"
                return ans

        if "fondazione irccs" in hco_norm and "milan" in city_value.lower():
            ans = dept_value, "Fondazione IRCCS Istituto Nazionale dei Tumori", "Milano"
            return ans

        if city_value.lower() == "bari":
            if "azienda ospedale policlinico" in hco_norm:
                ans = dept_value, "Azienda Osp Policlinico Consorziale", "Bari"
                return ans
            elif "irccs" in hco_norm:
                ans = dept_value, "IRCCS Oncologico Bari", "Bari"
                return ans

        if "san raffaele" in hco_norm and "milan" in city_value.lower():
            if any(alias in hco_norm for alias in ["hospital","ospedale","scientific institute","ircss"]):
                ans = dept_value, "IRCCS  S. Raffaele - Milano", "Milano"
                return ans
            elif any(alias in hco_norm for alias in ["university","università","universita","research centre","institute"]):
                ans = dept_value, "Vita-Salute San Raffaele University", "Milano"
                return ans

        if "humanitas" in hco_norm:
            if "milan" in city_value.lower() or "biology resource center" in hco_norm:
                ans = dept_value, "Humanitas University", "Milano"
            elif "irccs" in hco_norm or "rozzano" in city_value.lower():
                ans = dept_value, "Humanitas Clinical and Research Center-IRCCS", "Rozzano"
            elif "gavazzeni" in hco_norm:
                ans = dept_value, "Humanitas Gavazzeni", "Bergamo"
            elif "catanese" in hco_norm or "misterbianco" in city_value.lower():
                ans = dept_value, "Humanitas Istituto Clinico Catanese", "Misterbianco"
            return ans

        if "umberto" in hco_norm or "policlinico u i" in hco_norm:
            if "rom" in city_value.lower():
                ans = dept_value, "Policlinico Umberto I - Roma", "Roma"
                return ans
            if "torino" == city_value.lower() or "turin" == city_value.lower():
                ans = dept_value, "Ospedale Mauriziano  Umberto I - Torino", "Torino"
                return ans
            if "enna" in city_value.lower():
                ans = dept_value, "Azienda Ospedaliera Umberto I - Enna", "Enna"
                return ans
            if "nocera inferiore" in city_value.lower():
                ans = dept_value, "P.O. Umberto I - Nocera Inferiore", "Nocera Inferiore"
                return ans

        if "andrea" in hco_norm:
            sant_andrea_alias = {}
            if "rom" in city_value.lower():
                sant_andrea_alias = {
                    "s andrea hospital": ("Azienda Ospedaliera Sant`Andrea - Roma", "Roma"),
                    "st andrea hospital": ("Azienda Ospedaliera Sant`Andrea - Roma", "Roma"),
                    "santandrea hospital": ("Azienda Ospedaliera Sant`Andrea - Roma", "Roma"),
                    "sant andrea hospital": ("Azienda Ospedaliera Sant`Andrea - Roma", "Roma"),
                    "santo andrea hospital": ("Azienda Ospedaliera Sant`Andrea - Roma", "Roma"),
                    "santandrea university hospital": ("Azienda Ospedaliera Sant`Andrea - Roma", "Roma"),
                    "sant andrea university hospital": ("Azienda Ospedaliera Sant`Andrea - Roma", "Roma"),
                    "st andrea university hospital": ("Azienda Ospedaliera Sant`Andrea - Roma", "Roma"),
                    "azienda ospedaliera universitaria sant'andrea": ("Azienda Ospedaliera Sant`Andrea - Roma", "Roma"),
                    "university hospital santandrea": ("Azienda Ospedaliera Sant`Andrea - Roma", "Roma"),
                }
            elif "spezia" in city_value.lower():
                sant_andrea_alias = {
                    "santandrea hospital": ("Ospedale Sant`Andrea - La Spezia", "La Spezia"),
                    "hospital s andrea la": ("Ospedale Sant`Andrea - La Spezia", "La Spezia"),
                }
            for alias, (fixed_hco, fixed_city) in sant_andrea_alias.items():
                if alias in hco_norm:
                    ans = dept_value, fixed_hco, fixed_city
                    return ans

            if hco_norm == "fondazione policlinico universitario" and "rom" in city_value.lower():
                ans = dept_value, "IRCCS Policlinico Universitario A. Gemelli", "Roma"
                return ans

            if "catholic university" in hco_norm and "rom" in hco_norm.lower():
                ans = dept_value,"Università Cattolica del Sacro Cuore", "Roma"
                return ans

            if "chiara" in hco_norm and "trento" in hco_norm.lower():
                ans = dept_value,"Ospedale Santa Chiara di Trento", "Trento"
                return ans

            if "childrens hospital" in hco_norm and ("florence" in hco_norm.lower() or "firenze" in hco_norm.lower()):
                ans = dept_value, "Azienda Ospedaliera Meyer", "Firenze"
                return ans

            if "santanna hospital" in hco_norm and "ferrara" in hco_norm.lower():
                ans = dept_value, "Arcispedale Sant'Anna", "Ferrara"
                return ans


        alias_map = {
                "poliambulanza": ("Fondazione Poliambulanza - Brescia", "Brescia"),

                "università di brescia": ("University of Brescia", "Brescia"),

                "verona university hospital": ("Azienda Ospedaliera Di Verona", "Verona"),
                "university of verona hospital": ("Azienda Ospedaliera Di Verona", "Verona"),
                "university hospital of verona": ("Azienda Ospedaliera Di Verona", "Verona"),
                "university hospital verona": ("Azienda Ospedaliera Di Verona", "Verona"),
                "university and hospital trust of verona": ("Azienda Ospedaliera Di Verona", "Verona"),
                "university hospital trust of verona": ("Azienda Ospedaliera Di Verona", "Verona"),
                "university hospital integrated trust of verona": ("Azienda Ospedaliera Di Verona", "Verona"),
                "verona medical school": ("Azienda Ospedaliera Di Verona", "Verona"),
                "verona hospital trust": ("Azienda Ospedaliera Di Verona", "Verona"),
                "university of verona verona hospital": ("Azienda Ospedaliera Di Verona", "Verona"),
                "university trust of verona": ("Azienda Ospedaliera Di Verona", "Verona"),
                "university and hospital trust": ("Azienda Ospedaliera Di Verona", "Verona"),
                "verona integrated university hospital": ("Azienda Ospedaliera Di Verona", "Verona"),
                "university of verona and hospital trust": ("Azienda Ospedaliera Di Verona", "Verona"),
                "aoui verona": ("Azienda Ospedaliera Di Verona", "Verona"),
                "azienda ospedaliera integrata dell'università di verona": ("Azienda Ospedaliera Di Verona", "Verona"),

                "università degli studi di verona": ("University of Verona", "Verona"),
                "universita degli studi di verona": ("University of Verona", "Verona"),
                "university of verona": ("University of Verona", "Verona"),
                "verona university": ("University of Verona", "Verona"),
                "aovrveneto": ("University of Verona", "Verona"),

                "gb rossi": ("Azienda Ospedaliera Universitaria Integrata di Verona", "Verona"),
                "rossi university hospital": ("Azienda Ospedaliera Universitaria Integrata di Verona", "Verona"),
                "borgoroma hospital": ("Azienda Ospedaliera Universitaria Integrata di Verona", "Verona"),

                "pederzoli hospital": ("Casa di Cura Privata Ospedale P. Pederzoli", "Verona"),
                "hospital casa di cura pederzoli": ("Casa di Cura Privata Ospedale P. Pederzoli", "Verona"),

                "mater salutis hospital": ("Ospedale Mater Salutis", "Verona"),

                "azienda ospedaliero universitaria pisana": ("Azienda Ospedaliero-Universitaria Pisana", "Pisa"),
                "pisa university hospital": ("Azienda Ospedaliero-Universitaria Pisana", "Pisa"),
                "university hospital of pisa": ("Azienda Ospedaliero-Universitaria Pisana", "Pisa"),
                "university of pisa medical school hospital": ("Azienda Ospedaliero-Universitaria Pisana", "Pisa"),
                "university of pisa hospital": ("Azienda Ospedaliero-Universitaria Pisana", "Pisa"),
                "faculty of medicine hospital of the university of pisa": ("Azienda Ospedaliero-Universitaria Pisana","Pisa"),
                "aou pisana": ("Azienda Ospedaliero-Universitaria Pisana", "Pisa"),
                "universitaria dellospedale di cisanello": ("Azienda Ospedaliero-Universitaria Pisana", "Pisa"),

                "università degli studi di pisa": ("University of Pisa", "Pisa"),
                "universita degli studi di pisa": ("University of Pisa", "Pisa"),
                "università di pisa": ("University of Pisa", "Pisa"),
                "universita di pisa": ("University of Pisa", "Pisa"),
                "pisa university": ("University of Pisa", "Pisa"),

                "fondazione pisana per la scienza": ("Fondazione Pisana per la Scienza ONLUS", "Pisa"),
                "fondazione pisa per la scienza": ("Fondazione Pisana per la Scienza ONLUS", "Pisa"),

                "casa di cura san rossore": ("Casa Di Cura Privata San Rossore S.R.L.", "Pisa"),

                "miulli": ("Ospedale Miulli", "Bari"),

                "university of bari": ("University of Bari", "Bari"),
                "aldo moro": ("University of Bari", "Bari"),
                "a moro": ("University of Bari", "Bari"),

                "consorziale policlinico": ("Azienda Osp Policlinico Consorziale", "Bari"),
                "policlinico consorziale": ("Azienda Osp Policlinico Consorziale", "Bari"),
                "policlinico of bari": ("Azienda Osp Policlinico Consorziale", "Bari"),
                "policlinico di bari": ("Azienda Osp Policlinico Consorziale", "Bari"),
                "policlinico bari": ("Azienda Osp Policlinico Consorziale", "Bari"),
                "polyclinic hospital of bari": ("Azienda Osp Policlinico Consorziale", "Bari"),
                "bari policlinico": ("Azienda Osp Policlinico Consorziale", "Bari"),
                "university hospital of bari": ("Azienda Osp Policlinico Consorziale", "Bari"),

                "giovanni paolo ii": ("IRCCS Oncologico Bari", "Bari"),
                "bellis": ("IRCCS Oncologico Bari", "Bari"),

                "lum university": ("LUM University", "Bari"),
                "di venere": ("P.O. Bari Sud", "Bari"),
                "giovanni xxiii": ("Ospedale Pediatrico Giovanni XXIII Bari", "Bari"),

                "perrino": ("Stabilimento Perrino", "Brindisi"),

                "san raffaele irccs": ("IRCCS  S. Raffaele - Milano", "Milano"),
                "san raffaele hospital irccs": ("IRCCS  S. Raffaele - Milano", "Milano"),
                "irccs san raffaele": ("IRCCS  S. Raffaele - Milano", "Milano"),
                "san raffaele scientific institute irccs": ("IRCCS  S. Raffaele - Milano", "Milano"),
                "irccs ospedale san raffaele": ("IRCCS  S. Raffaele - Milano", "Milano"),
                "hospital san raffaelle": ("IRCCS  S. Raffaele - Milano", "Milano"),

                "vanvitelli hospital": ("Azienda Ospedaliera Universitaria Luigi Vanvitelli", "Milano"),
                "aou university of campania luigi vanvitelli": ("Azienda Ospedaliera Universitaria Luigi Vanvitelli", "Milano"),
                "aou vanvitelli": ("Azienda Ospedaliera Universitaria Luigi Vanvitelli", "Milano"),

                "luigi vanvitelli university": ("University of Campania Luigi Vanvitelli", "Milano"),
                "università degli studi della campania luigi vanvitelli": ("University of Campania Luigi Vanvitelli", "Milano"),
                "universita degli studi della campania luigi vanvitelli": ("University of Campania Luigi Vanvitelli", "Milano"),
                "università della campania luigi vanvitelli": ("University of Campania Luigi Vanvitelli", "Milano"),
                "università degli studi della campania l vanvitelli": ("University of Campania Luigi Vanvitelli", "Milano"),
                "university of campania l vanvitelli": ("University of Campania Luigi Vanvitelli", "Milano"),
                "university of study of campania luigi vanvitelli": ("University of Campania Luigi Vanvitelli", "Milano"),
                "university of study of campania l vanvitelli": ("University of Campania Luigi Vanvitelli", "Milano"),
                "university of campania lvanvitelli": ("University of Campania Luigi Vanvitelli", "Milano"),
                "university of campania luigi vanvitelli": ("University of Campania Luigi Vanvitelli", "Milano"),
                "university of study of campania": ("University of Campania Luigi Vanvitelli", "Milano"),

                "grande ospedale metropolitano niguarda": ("ASST Grande Ospedale Metropolitano Niguarda", "Milano"),
                "niguarda hospital": ("ASST Grande Ospedale Metropolitano Niguarda", "Milano"),
                "niguarda ca granda hospital": ("ASST Grande Ospedale Metropolitano Niguarda", "Milano"),
                "niguarda cagranda hospital": ("ASST Grande Ospedale Metropolitano Niguarda", "Milano"),
                "niguardacà granda hospital": ("ASST Grande Ospedale Metropolitano Niguarda", "Milano"),
                "niguarda nigurda hospital": ("ASST Grande Ospedale Metropolitano Niguarda", "Milano"),
                "niguardacàgranda hospital": ("ASST Grande Ospedale Metropolitano Niguarda", "Milano"),
                "asst grande ospedale niguarda": ("ASST Grande Ospedale Metropolitano Niguarda", "Milano"),
                "milano niguarda university": ("ASST Grande Ospedale Metropolitano Niguarda", "Milano"),


                "fondazione irccs istituto nazionale dei tumori di milano": ("Fondazione IRCCS Istituto Nazionale dei Tumori", "Milano"),
                "fondazione irccs istituto nazionale dei tumori milan": ("Fondazione IRCCS Istituto Nazionale dei Tumori", "Milano"),
                "fondazione istituto nazionale tumori irccs": ("Fondazione IRCCS Istituto Nazionale dei Tumori", "Milano"),
                "irccs istituto nazionale tumori int": ("Fondazione IRCCS Istituto Nazionale dei Tumori", "Milano"),
                "irccs foundation national cancer institute": ("Fondazione IRCCS Istituto Nazionale dei Tumori", "Milano"),
                "foundation irccs national cancer institute": ("Fondazione IRCCS Istituto Nazionale dei Tumori", "Milano"),
                "fondazione ircss istituto nazionale dei tumori": ("Fondazione IRCCS Istituto Nazionale dei Tumori", "Milano"),
                "istituto nazionale tumori milano": ("Fondazione IRCCS Istituto Nazionale dei Tumori", "Milano"),

                "european institute of oncology irccs": ("IRCCS European Institute of Oncology", "Milano"),
                "european institute of oncology ieo irccs": ("IRCCS European Institute of Oncology", "Milano"),
                "irccs european institute of oncology": ("IRCCS European Institute of Oncology", "Milano"),
                "irccs ieo european institute of oncology": ("IRCCS European Institute of Oncology", "Milano"),
                "european institute of oncology hospital and institute for scientific treatment": ("IRCCS European Institute of Oncology", "Milano"),

                "università di milano": ("University of Milano", "Milano"),
                "university of milan": ("University of Milano", "Milano"),
                "università degli studi di milano": ("University of Milano", "Milano"),

                "l sacco hospital": ("ASST Fatebenefratelli Sacco", "Milano"),
                "luigi sacco hospital": ("ASST Fatebenefratelli Sacco", "Milano"),
                "asst fatebenefratelli sacco university hospital": ("ASST Fatebenefratelli Sacco", "Milano"),

                "hospital vittore buzzi": ("Children's Hospital Vittore Buzzi", "Milano"),
                "vittore buzzi hospital": ("Children's Hospital Vittore Buzzi", "Milano"),

                "asstsanti paolo e carlo university hospital": ("ASST SANTI PAOLO E CARLO", "Milano"),

                "vita e salute university": ("Vita-Salute San Raffaele University", "Milano"),

                "milanobicocca university": ("University of Milano-Bicocca", "Milano"),
                "milano bicocca university": ("University of Milano-Bicocca", "Milano"),
                "university of bicocca": ("University of Milano-Bicocca", "Milano"),
                "universita degli studi di milanobicocca": ("University of Milano-Bicocca", "Milano"),
                "italy università milanobicocca": ("University of Milano-Bicocca", "Milano"),

                "polytechnic university of milano": ("Politecnico di Milano", "Milano"),

                "university of milano statale": ("Università degli Studi di Milano", "Milano"),
                "university of milan school of medicine": ("Università degli Studi di Milano", "Milano"),
                "universitadegli studi di milano": ("Università degli Studi di Milano", "Milano"),

                "granda ospedale maggiore policlinico": ("Fondazione IRCCS Ca' Granda Ospedale Maggiore Policlinico", "Milano"),
                "cà granda fondazione ospedale maggiore policlinico": ("Fondazione IRCCS Ca' Granda Ospedale Maggiore Policlinico", "Milano"),
                "ca granda fondazione ospedale maggiore policlinico": ("Fondazione IRCCS Ca' Granda Ospedale Maggiore Policlinico", "Milano"),
                "policlinico di milano": ("Fondazione IRCCS Ca' Granda Ospedale Maggiore Policlinico", "Milano"),

                "irccs auxologic italian institute": ("Auxologico IRCCS - Ricerca e cura per la tua salute", "Milano"),
                "istituto auxologico italiano": ("Auxologico IRCCS - Ricerca e cura per la tua salute", "Milano"),



                "mario negri institut": ("Mario Negri Institute for Pharmacological Research", "Milano"),
                "mario negri istituto di ricovero": ("Mario Negri Institute for Pharmacological Research", "Milano"),
                "istituto di ricerche farmacologiche mario negri": ("Mario Negri Institute for Pharmacological Research", "Milano"),
                "instituto di ricerche farmacologiche mario negri": ("Mario Negri Institute for Pharmacological Research", "Milano"),
                "instituto di richerche farmachologiche mario negri": ("Mario Negri Institute for Pharmacological Research", "Milano"),

                "san carlo borromeo hospital": ("Ospedale San Carlo Borromeo di Milano", "Milano"),

                "centro cardiologico monzino": ("Centro Cardiologico Monzino IRCCS", "Milano"),

                "asst santi carlo e paolo milan": ("ASST Santi Paolo e Carlo", "Milano"),

                "polistudium": ("Polistudium SRL", "Milano"),

                "g pini hospital": ("ASST Pini-CTO - Presidio Gaetano Pini", "Milano"),

                "gfornaroli hospital": ("Ospedale G. Fornaroli Magenta", "Milano"),

                "san gerardo hospital": ("IRCCS San Gerardo dei Tintori", "Monza"),
                "san gerardo university hospital": ("IRCCS San Gerardo dei Tintori", "Monza"),
                "irccs fondazione san gerardo": ("IRCCS San Gerardo dei Tintori", "Monza"),
                "irccs san gerardo": ("IRCCS San Gerardo dei Tintori", "Monza"),
                "ospedale san gerardo": ("IRCCS San Gerardo dei Tintori", "Monza"),

                "policlinico di monza": ("Policlinico di Monza", "Monza"),

                "rho asst rhodense": ("ASST Rhodense", "Rho"),
                "rho hospital": ("ASST Rhodense", "Rho"),
                "rho and garbagnate milanese hospital": ("ASST Rhodense", "Rho"),
                "presidio ospedaliero di rho": ("ASST Rhodense", "Rho"),

                "garbagnate milanese hospital": ("Guido Salvini Hospital in Garbagnate Milanese", "Garbagnate Milanese"),

                "irccs policlinico san donato": ("IRCCS Policlinico San Donato", "San Donato Milanese"),
                "san donato hospital": ("IRCCS Policlinico San Donato", "San Donato Milanese"),
                "irccs polyclinic san donato": ("IRCCS Policlinico San Donato", "San Donato Milanese"),

                "padova university hospital": ("Azienda Ospedaliera Di Padova", "Padova"),
                "university hospital of padova": ("Azienda Ospedaliera Di Padova", "Padova"),
                "padova teaching hospital": ("Azienda Ospedaliera Di Padova", "Padova"),
                "hospital of the university of padova": ("Azienda Ospedaliera Di Padova", "Padova"),
                "university and hospital of padova": ("Azienda Ospedaliera Di Padova", "Padova"),
                "azienda ospedale università padova": ("Azienda Ospedaliera Di Padova", "Padova"),
                "azienda ospedaleuniversità di padova": ("Azienda Ospedaliera Di Padova", "Padova"),
                "azienda ospedalierauniversità di padova": ("Azienda Ospedaliera Di Padova", "Padova"),
                "azienda ospedalierouniversità di padova": ("Azienda Ospedaliera Di Padova", "Padova"),
                "padua university hospital": ("Azienda Ospedaliera Di Padova", "Padova"),
                "university hospital of padua": ("Azienda Ospedaliera Di Padova", "Padova"),
                "padua universityhospital": ("Azienda Ospedaliera Di Padova", "Padova"),
                "university hospital padua": ("Azienda Ospedaliera Di Padova", "Padova"),
                "azienda ospedaliera universitaria": ("Azienda Ospedaliera Di Padova", "Padova"),

                "san carlo hospital": ("San Carlo Azienda Ospedaliera Regionale", "Potenza"),
                "aor san carlo": ("San Carlo Azienda Ospedaliera Regionale", "Potenza"),

                "desio hospital": ("Ospedale Di Circolo - Desio", "Desio"),

                "university of padova": ("University of Padova", "Padova"),
                "università degli studi di padova": ("University of Padova", "Padova"),
                "padova university": ("University of Padova", "Padova"),
                "university of padua": ("University of Padova", "Padova"),
                "padua university": ("University of Padova", "Padova"),

                "veneto institute of oncology": ("Istituto Oncologico Veneto", "Padova"),
                "iovirccs": ("Istituto Oncologico Veneto", "Padova"),
                "iov irccs": ("Istituto Oncologico Veneto", "Padova"),
                "istituto oncologico veneto": ("Istituto Oncologico Veneto", "Padova"),


                "university hospital of marche": ("A.O.U.Ospedali Riuniti - Ancona", "Ancona"),
                "united hospital of ancona": ("A.O.U.Ospedali Riuniti - Ancona", "Ancona"),
                "azienda ospedalierouniversitaria delle marche": ("A.O.U.Ospedali Riuniti - Ancona", "Ancona"),
                "azienda ospedaliero universitaria delle marche": ("A.O.U.Ospedali Riuniti - Ancona", "Ancona"),
                "ancona hospital": ("A.O.U.Ospedali Riuniti - Ancona", "Ancona"),
                "ospedali riuniti delle marche": ("A.O.U.Ospedali Riuniti - Ancona", "Ancona"),
                "aou ospedali riuniti": ("A.O.U.Ospedali Riuniti - Ancona", "Ancona"),
                "aou umberto ilancisisalesi": ("A.O.U.Ospedali Riuniti - Ancona", "Ancona"),
                "g salesi university hospital": ("A.O.U.Ospedali Riuniti - Ancona", "Ancona"),

                "università politecnica delle marche": ("Polytechnic University of Marche", "Ancona"),
                "polytechnic university of marche": ("Polytechnic University of Marche", "Ancona"),
                "marche polytechnic university": ("Polytechnic University of Marche", "Ancona"),

                "carlo urbani hospital": ("Ospedale Carlo Urbani", "Jesi"),

                "ospedale santa maria degli angeli adria": ("Ospedale Di Adria", "Adria"),

                "university hospital of alessandria": ("Az. Ss.Antonio E Biagio E C.Arrigo", "Alessandria"),
                "alessandria university hospital": ("Az. Ss.Antonio E Biagio E C.Arrigo", "Alessandria"),
                "ss antonio e biagio e cesare arrigo hospital": ("Az. Ss.Antonio E Biagio E C.Arrigo", "Alessandria"),
                "ss antonio e biagio general hospital": ("Az. Ss.Antonio E Biagio E C.Arrigo", "Alessandria"),
                "ospedale di alessandria": ("Az. Ss.Antonio E Biagio E C.Arrigo", "Alessandria"),
                "ss antonio e biagio e cesare arrigo of alessandria": ("Az. Ss.Antonio E Biagio E C.Arrigo", "Alessandria"),

                "università degli studi del piemonte orientale": ("Università degli Studi del Piemonte Orientale Amedeo Avogadro", "Alessandria"),
                "university of eastern piedmont amedeo avogadro": ("Università degli Studi del Piemonte Orientale Amedeo Avogadro", "Alessandria"),

                "viale del policlinico" : ("Policlinico Umberto I - Roma", "Roma"),
                "policlinico umberto i" : ("Policlinico Umberto I - Roma", "Roma"),

                "gemelli irccs" : ("IRCCS Policlinico Universitario A. Gemelli", "Roma"),
                "irccs a gemelli" : ("IRCCS Policlinico Universitario A. Gemelli", "Roma"),
                "gemelli university hospital" : ("IRCCS Policlinico Universitario A. Gemelli", "Roma"),
                "gemelli science and technology park" : ("IRCCS Policlinico Universitario A. Gemelli", "Roma"),
                "policlinico universitario agostino gemelli" : ("IRCCS Policlinico Universitario A. Gemelli", "Roma"),
                "policlinico universitario a gemelli" : ("IRCCS Policlinico Universitario A. Gemelli", "Roma"),
                "policlinico universitario agemelli" : ("IRCCS Policlinico Universitario A. Gemelli", "Roma"),
                "policlinico gemelli" : ("IRCCS Policlinico Universitario A. Gemelli", "Roma"),
                "policlinico agostino gemelli" : ("IRCCS Policlinico Universitario A. Gemelli", "Roma"),
                "policlinic universitario a gemelli" : ("IRCCS Policlinico Universitario A. Gemelli", "Roma"),
                "foundation a gemelli hospital" : ("IRCCS Policlinico Universitario A. Gemelli", "Roma"),
                "hospital foundation a gemelli" : ("IRCCS Policlinico Universitario A. Gemelli", "Roma"),
                "largo agostino gemelli" : ("IRCCS Policlinico Universitario A. Gemelli", "Roma"),
                "fondazione policlinico universitario agostino" : ("IRCCS Policlinico Universitario A. Gemelli", "Roma"),



                "irccs fondazione santa lucia" : ("IRCCS S. Lucia", "Roma"),
                "irccs santa lucia foundation" : ("IRCCS. S. Lucia", "Roma"),

                "saint camillus international university" : ("UniCamillus University", "Roma"),
                "unicamillus international medical university" : ("UniCamillus University", "Roma"),
                "unicamillus international university" : ("UniCamillus University", "Roma"),

                "ospedale isola tiberina gemelli" : ("Ospedale Fatebenefatelli-Isola Tiberina", "Roma"),

                "campus biomedico" : ("Fondazione Policlinico Universitario Campus Bio-Medico", "Roma"),
                "campus bio medico" : ("Fondazione Policlinico Universitario Campus Bio-Medico", "Roma"),
                "medico of rome university" : ("Fondazione Policlinico Universitario Campus Bio-Medico", "Roma"),
                "medico university of rome" : ("Fondazione Policlinico Universitario Campus Bio-Medico", "Roma"),
                "biomedico university of rome" : ("Fondazione Policlinico Universitario Campus Bio-Medico", "Roma"),

                "san camillo forlanini hospital" : ("Azienda Ospedaliera San Camillo Forlanini", "Roma"),
                "san camilloforlanini hospital" : ("Azienda Ospedaliera San Camillo Forlanini", "Roma"),
                "san camillo hospital" : ("Azienda Ospedaliera San Camillo Forlanini", "Roma"),
                "s camillo hospital" : ("Azienda Ospedaliera San Camillo Forlanini", "Roma"),
                "s camillo forlanini hospital" : ("Azienda Ospedaliera San Camillo Forlanini", "Roma"),
                "san camilloforlanini general hospital" : ("Azienda Ospedaliera San Camillo Forlanini", "Roma"),
                "s camilloforlanini hospital" : ("Azienda Ospedaliera San Camillo Forlanini", "Roma"),
                "ospedale san camillo" : ("Azienda Ospedaliera San Camillo Forlanini", "Roma"),
                "saint camillus hospital" : ("Azienda Ospedaliera San Camillo Forlanini", "Roma"),
                "san camilloforlanini regional hospital" : ("Azienda Ospedaliera San Camillo Forlanini", "Roma"),

                "gesù childrens hospital" : ("bambino gesù childrens hospital", "Roma"),
                "hospital bambino gesù" : ("bambino gesù childrens hospital", "Roma"),
                "bambino gesu childrens hospital" : ("bambino gesù childrens hospital", "Roma"),
                "hospital san paolo" : ("bambino gesù childrens hospital", "Roma"),

                "policlinico tor vergata" : ("Azienda Ospedaliera Universitaria Policlinico Tor Vergata", "Roma"),
                "tor vergata university hospital" : ("Azienda Ospedaliera Universitaria Policlinico Tor Vergata", "Roma"),

                "regina elena national cancer institute" : ("IRCCS Istituto Nazionale Tumori Regina Elena", "Roma"),
                "regina elena national cancer institutre" : ("IRCCS Istituto Nazionale Tumori Regina Elena", "Roma"),
                "istituto nazionale tumori regina elena" : ("IRCCS Istituto Nazionale Tumori Regina Elena", "Roma"),

                "nuovo regina margherita hospital" : ("Presidio Nuovo Regina Margherita", "Roma"),

                "san giovanni hospital" : ("Azienda Ospedaliera San Giovanni Addolorata", "Roma"),
                "san giovanni addolorata hospital" : ("Azienda Ospedaliera San Giovanni Addolorata", "Roma"),

                "s spirito hospital" : ("Ospedale Santo Spirito In Sassia", "Roma"),

                "s filippo neri hospital" : ("Ospedale San Filippo Neri", "Roma"),
                "san filippo neri hospital" : ("Ospedale San Filippo Neri", "Roma"),

                "sandro pertini hospital" : ("Ospedale Sandro Pertini", "Roma"),

                "s eugenio hospital" : ("Ospedale SantEugenio", "Roma"),

                "gb grassi hospital" : ("Presidio Ospedaliero G.B. Grassi", "Roma"),

                "irccs san gallicano dermatological institute" : ("IRCCS Instituto Dermatologico San Gallicano", "Roma"),

                "policlinico casilino" : ("Ospedale Policlinico Casilino", "Roma"),

                "university of rome tor" : ("University of Roma Tor Vergata", "Roma"),
                "tor vergata university" : ("University of Roma Tor Vergata", "Roma"),
                "university of tor vergata" : ("University of Roma Tor Vergata", "Roma"),
                "university of roma tor vergata" : ("University of Roma Tor Vergata", "Roma"),
                "university tor vergata" : ("University of Roma Tor Vergata", "Roma"),
                "university of rometor vergata" : ("University of Roma Tor Vergata", "Roma"),


                "catholic university of the sacred heart" : ("Università Cattolica del Sacro Cuore", "Roma"),
                "università cattolica del sacro" : ("Università Cattolica del Sacro Cuore", "Roma"),
                "catholic university of rome" : ("Università Cattolica del Sacro Cuore", "Roma"),

                "university roma tre": ("Roma Tre University", "Roma"),
                "roma tre university": ("Roma Tre University", "Roma"),
                "università roma tre": ("Roma Tre University", "Roma"),

                "link campus university": ("Link Campus University", "Roma"),

                "sapienza university": ("Sapienza University of Roma", "Roma"),
                "sapienza università": ("Sapienza University of Roma", "Roma"),
                "university of rome sapienza": ("Sapienza University of Roma", "Roma"),
                "university of rome la sapienza": ("Sapienza University of Roma", "Roma"),
                "university sapienza": ("Sapienza University of Roma", "Roma"),
                "university la sapienza": ("Sapienza University of Roma", "Roma"),
                "university roma la sapienza": ("Sapienza University of Roma", "Roma"),
                "sapienza school of medicine": ("Sapienza University of Roma", "Roma"),
                "university of rome": ("Sapienza University of Roma", "Roma"),
                "università di roma": ("Sapienza University of Roma", "Roma"),

                "irccs azienda ospedalierouniversitaria di bologna" : ("IRCCS Azienda Ospedaliero - Universitaria di Bologna", "Bologna"),
                "ircss istituto di scienze neurologiche di bologna" : ("IRCCS Azienda Ospedaliero - Universitaria di Bologna", "Bologna"),
                "irccsistituto delle scienze neurologiche di bologna": ("IRCCS Azienda Ospedaliero - Universitaria di Bologna", "Bologna"),
                "aoubo" : ("IRCCS Azienda Ospedaliero - Universitaria di Bologna", "Bologna"),
                "irccs azienda ospedalierouniversitaria santorsola" : ("IRCCS Azienda Ospedaliero - Universitaria di Bologna", "Bologna"),
                "irccs azienda ospedalierauniversitaria bologna" : ("IRCCS Azienda Ospedaliero - Universitaria di Bologna", "Bologna"),
                "irccs azienda ospedalierouniversitaria of bologna" : ("IRCCS Azienda Ospedaliero - Universitaria di Bologna", "Bologna"),
                "aou bologna" : ("IRCCS Azienda Ospedaliero - Universitaria di Bologna", "Bologna"),
                "aou di bologna" : ("IRCCS Azienda Ospedaliero - Universitaria di Bologna", "Bologna"),
                "aou of bologna": ("IRCCS Azienda Ospedaliero - Universitaria di Bologna", "Bologna"),
                "santorsola irccs": ("IRCCS Azienda Ospedaliero - Universitaria di Bologna", "Bologna"),
                "sorsola malpighi": ("IRCCS Azienda Ospedaliero - Universitaria di Bologna", "Bologna"),
                "s orsola malpighi": ("IRCCS Azienda Ospedaliero - Universitaria di Bologna", "Bologna"),
                "irccs santorsola": ("IRCCS Azienda Ospedaliero - Universitaria di Bologna", "Bologna"),
                "orsolamalpighi" : ("IRCCS Azienda Ospedaliero - Universitaria di Bologna", "Bologna"),
                "orsola malpighi" : ("IRCCS Azienda Ospedaliero - Universitaria di Bologna", "Bologna"),
                "santorsola malphigi" : ("IRCCS Azienda Ospedaliero - Universitaria di Bologna", "Bologna"),
                "santorsola university research hospital" : ("IRCCS Azienda Ospedaliero - Universitaria di Bologna", "Bologna"),
                "azienda ospedaliero universitaria di bologna" : ("IRCCS Azienda Ospedaliero - Universitaria di Bologna", "Bologna"),

                "university of bologna" : ("University of Bologna", "Bologna"),
                "università di bologna" : ("University of Bologna", "Bologna"),
                "alma mater" : ("University of Bologna", "Bologna"),
                "bologna university" : ("University of Bologna", "Bologna"),

                "madre fortunata toniolo" : ("Casa Di Cura Madre Fortunata Toniolo", "Bologna"),

                "morgagnipierantoni hospital" : ("Presidio Ospedaliero Forlì", "Forlì"),
                "morgagni pierantoni" : ("Presidio Ospedaliero Forlì", "Forlì"),
                "pierantoni hospital" : ("Presidio Ospedaliero Forlì", "Forlì"),

                "university hospital of modena" : ("Azienda Ospedaliera Policlinico", "Modena"),
                "university hospital modena" : ("Azienda Ospedaliera Policlinico", "Modena"),
                "modena university hospital" : ("Azienda Ospedaliera Policlinico", "Modena"),
                "universityhospital of modena" : ("Azienda Ospedaliera Policlinico", "Modena"),
                "azienda ospedaliero universitaria policlinico di modena" : ("Azienda Ospedaliera Policlinico", "Modena"),
                "azienda ospedaliero universitaria di modena" : ("Azienda Ospedaliera Policlinico", "Modena"),
                "azienda ospedalierouniversitaria di modena" : ("Azienda Ospedaliera Policlinico", "Modena"),
                "ospedalierouniversitaria policlinico di modena" : ("Azienda Ospedaliera Policlinico", "Modena"),
                "policlinico of modena" : ("Azienda Ospedaliera Policlinico", "Modena"),
                "policlinico modena" : ("Azienda Ospedaliera Policlinico", "Modena"),
                "policlinico di modena" : ("Azienda Ospedaliera Policlinico", "Modena"),

                "baggiovara civil hospital" : ("Ospedale Civile di Baggiovara", "Baggiovara"),

                "university of modena" : ("Ospedale Civile di Baggiovara", "Baggiovara"),

                "careggi university hospital" : ("Az. Ospedaliero Universitaria - Careggi", "Firenze"),
                "university hospital careggi" : ("Az. Ospedaliero Universitaria - Careggi", "Firenze"),
                "azienda ospedaliero universitaria careggi" : ("Az. Ospedaliero Universitaria - Careggi", "Firenze"),
                "azienda ospedalierouniversitaria careggi" : ("Az. Ospedaliero Universitaria - Careggi", "Firenze"),
                "azienda ospedalierauniversitaria careggi" : ("Az. Ospedaliero Universitaria - Careggi", "Firenze"),
                "aou careggi" : ("Az. Ospedaliero Universitaria -  Careggi", "Firenze"),
                "careggi hospital" : ("Az. Ospedaliero Universitaria -  Careggi", "Firenze"),
                "university hospital of florence" : ("Az. Ospedaliero Universitaria -  Careggi", "Firenze"),


                "university of florence" : ("University of Firenze", "Firenze"),
                "university of firenze" : ("University of Firenze", "Firenze"),
                "università di firenze" : ("University of Firenze", "Firenze"),
                "università degli studi di firenze" : ("University of Firenze", "Firenze"),
                "university of refereflorence" : ("University of Firenze", "Firenze"),

                "azienda ospedalierouniversitaria meyer" : ("Azienda Ospedaliera Meyer", "Firenze"),
                "azienda ospedaliero universitaria meyer" : ("Azienda Ospedaliera Meyer", "Firenze"),
                "meyer childrens hospita" : ("Azienda Ospedaliera Meyer", "Firenze"),
                "meyer children hospita" : ("Azienda Ospedaliera Meyer", "Firenze"),

                "f.i.r.m.o": ("FIRMO - Italian Foundation for Research on Bone Diseases", "Firenze"),
                "firmo foundation": ("FIRMO - Italian Foundation for Research on Bone Diseases", "Firenze"),
                "firmo onlus": ("FIRMO - Italian Foundation for Research on Bone Diseases", "Firenze"),
                "italian foundation for the research on bone diseases": ("FIRMO - Italian Foundation for Research on Bone Diseases", "Firenze"),

                "hospital of prato": ("Nuovo Ospedale Santo Stefano di Prato", "Firenze"),

                "villa donatello hospital" : ("Casa Di Cura Villa Donatello Spa", "Sesto Fiorentino"),
                "hospital villa donatello" : ("Casa Di Cura Villa Donatello Spa", "Sesto Fiorentino"),

                "irccsismett" : ("IRCCS ISMETT – UPMC", "Parlemo"),
                "irccs ismett" : ("IRCCS ISMETT – UPMC", "Parlemo"),
                "university of pittsburgh medical center" : ("IRCCS ISMETT – UPMC", "Parlemo"),

                "university hospital of palermo" : ("Azienda Ospedaliera Universitaria Palermo", "Parlemo"),
                "p giaccone university hospital" : ("Azienda Ospedaliera Universitaria Palermo", "Parlemo"),
                "university hospital paolo giaccone" : ("Azienda Ospedaliera Universitaria Palermo", "Parlemo"),
                "university hospital policlinico p giaccone" : ("Azienda Ospedaliera Universitaria Palermo", "Parlemo"),
                "paolo giaccone university hospital" : ("Azienda Ospedaliera Universitaria Palermo", "Parlemo"),
                "policlinico paolo giaccone" : ("Azienda Ospedaliera Universitaria Palermo", "Parlemo"),
                "policlinico universitario paolo giaccone" : ("Azienda Ospedaliera Universitaria Palermo", "Parlemo"),

                "arnas civico hospital" : ("Azienda Ospedaliera Civico Di Cristina", "Parlemo"),
                "arnas civico di cristina benfratelli hospital" : ("Azienda Ospedaliera Civico Di Cristina", "Parlemo"),
                "ospedale brotzu arnas" : ("Azienda Ospedaliera Civico Di Cristina", "Parlemo"),

                "university of palermo" : ("University of Palermo", "Parlemo"),
                "università degli studi di palermo" : ("University of Palermo", "Parlemo"),

                "azienda ospedalieraospedali riuniti villasofia cervello" : ("Ospedali Riuniti Villa Sofia - Cervello", "Parlemo"),

                "buccheri la ferla fatebenefratelli hospital" : ("Osp. Buccheri La Ferla Fatebenefratelli", "Parlemo"),

                "fpoirccs" : ("IRCCS Istituto Oncologico di Candiolo", "Candiolo"),
                "fpo irccs" : ("IRCCS Istituto Oncologico di Candiolo", "Candiolo"),
                "irccs candiolo" : ("IRCCS Istituto Oncologico di Candiolo", "Candiolo"),
                "candiolo cancer institute" : ("IRCCS Istituto Oncologico di Candiolo", "Candiolo"),

                "mauriziano hospital" : ("Ospedale Mauriziano  Umberto I - Torino", "Torino"),
                "mauriziano torino" : ("Ospedale Mauriziano  Umberto I - Torino", "Torino"),

                "azienda ospedaliero universitaria città della salute e della scienza di torino" : ("A.O.U. Citta della Salute e della Scienza di Torino", "Torino"),
                "azienda ospedaliero universitaria citta della salute e della scienza di torino" : ("A.O.U. Citta della Salute e della Scienza di Torino", "Torino"),
                "azienda ospedalierouniversitaria città della salute e della scienza di torino" : ("A.O.U. Citta della Salute e della Scienza di Torino", "Torino"),
                "azienda ospedalierouniversitaria città della salute e della scienza" : ("A.O.U. Citta della Salute e della Scienza di Torino", "Torino"),
                "città della salute e della scienza university hospital" : ("A.O.U. Citta della Salute e della Scienza di Torino", "Torino"),
                "città della salute e della scienza hospital" : ("A.O.U. Citta della Salute e della Scienza di Torino", "Torino"),
                "città della salute e della scienza universityhospital" : ("A.O.U. Citta della Salute e della Scienza di Torino", "Torino"),
                "university of turin and città della salute e della scienza hospital" : ("A.O.U. Citta della Salute e della Scienza di Torino", "Torino"),
                "turin university hospital" : ("A.O.U. Citta della Salute e della Scienza di Torino", "Torino"),
                "city of health and science university hospital" : ("A.O.U. Citta della Salute e della Scienza di Torino", "Torino"),
                "city of health and science hospital" : ("A.O.U. Citta della Salute e della Scienza di Torino", "Torino"),
                "molinette hospital" : ("A.O.U. Citta della Salute e della Scienza di Torino", "Torino"),
                "molinettesgas hospital" : ("A.O.U. Citta della Salute e della Scienza di Torino", "Torino"),

                "san giovanni bosco hospital" : ("Ospedale San Giovanni Bosco", "Torino"),

                "amedeo di savoia hospital" : ("Ospedale Amedeo Di Savoia", "Torino"),

                "university of turin" : ("University of Torino", "Torino"),
                "università degli studi di torino" : ("University of Torino", "Torino"),
                "universita degli studi di torino" : ("University of Torino", "Torino"),
                "center guido tarone" : ("University of Torino", "Torino"),

                "university hospital san luigi gonzaga": ("Azienda Ospedaliero-Universitaria San Luigi Gonzaga","Orbassano"),
                "san luigi hospital": ("Azienda Ospedaliero-Universitaria San Luigi Gonzaga", "Orbassano"),
                "san luigi gonzaga university hospital": ("Azienda Ospedaliero-Universitaria San Luigi Gonzaga","Orbassano"),
                "san luigi university hospital": ("Azienda Ospedaliero-Universitaria San Luigi Gonzaga", "Orbassano"),

                "federico ii university hospital": ("Azienda Ospedaliera Universitaria Federico II", "Napoli"),
                "uoc chirurgia endoscopica aou federico ii di napoli": ("Azienda Ospedaliera Universitaria Federico II", "Napoli"),
                "federico ii university medical school of naples": ("Azienda Ospedaliera Universitaria Federico II", "Napoli"),
                "aou federico ii": ("Azienda Ospedaliera Universitaria Federico II", "Napoli"),
                "university hospital federico ii": ("Azienda Ospedaliera Universitaria Federico II", "Napoli"),

                "federico ii university": ("University of Napoli Federico II", "Napoli"),
                "university of naples federico ii": ("University of Napoli Federico II", "Napoli"),
                "university federico ii": ("University of Napoli Federico II", "Napoli"),
                "university of federico ii": ("University of Napoli Federico II", "Napoli"),
                "università di napoli federico ii": ("University of Napoli Federico II", "Napoli"),
                "università federico ii di napoli": ("University of Napoli Federico II", "Napoli"),
                "università degli studi di napoli federico ii": ("University of Napoli Federico II", "Napoli"),
                "university of napoli federico ii": ("University of Napoli Federico II", "Napoli"),
                "università degli studi di napolifederico ii": ("University of Napoli Federico II", "Napoli"),
                "universitario monte s angelo": ("University of Napoli Federico II", "Napoli"),
                "universitario monte santangelo": ("University of Napoli Federico II", "Napoli"),

                "pausilipon hospital": ("Ospedale Pediatrico Santobono Pausilipon", "Napoli"),

                "g pascale irccs": ("Istituto Nazionale Tumori IRCCS Fondazione G. Pascale", "Napoli"),
                "irccsg pascale": ("Istituto Nazionale Tumori IRCCS Fondazione G. Pascale", "Napoli"),
                "fondazione g pascale": ("Istituto Nazionale Tumori IRCCS Fondazione G. Pascale", "Napoli"),
                "irccs fondazione pascale": ("Istituto Nazionale Tumori IRCCS Fondazione G. Pascale", "Napoli"),
                "irccs g pascale": ("Istituto Nazionale Tumori IRCCS Fondazione G. Pascale", "Napoli"),

                "cardarelli hospital": ("Ospedale Antonio Cardarelli", "Napoli"),
                "aorn cardarelli": ("Ospedale Antonio Cardarelli", "Napoli"),
                "aorn a cardarelli": ("Ospedale Antonio Cardarelli", "Napoli"),

                "policlinico san martino": ("IRCCS Azienda Ospedaliera Universitaria San Martino", "Genova"),
                "irccs aou san martino": ("IRCCS Azienda Ospedaliera Universitaria San Martino", "Genova"),
                "irccs university hospital san martino": ("IRCCS Azienda Ospedaliera Universitaria San Martino", "Genova"),

                "azienda ospedaliero universitaria di sassari": ("Azienda Ospedaliero Universitaria Sassari", "Sassari"),
                "azienda ospedalierouniversitaria of sassari": ("Azienda Ospedaliero Universitaria Sassari", "Sassari"),
                "azienda ospedaliero universitaria sassari": ("Azienda Ospedaliero Universitaria Sassari", "Sassari"),
                "azienda ospedalierouniversitaria di sassari": ("Azienda Ospedaliero Universitaria Sassari", "Sassari"),
                "aou of sassari": ("Azienda Ospedaliero Universitaria Sassari", "Sassari"),
                "university hospital of sassari": ("Azienda Ospedaliero Universitaria Sassari", "Sassari"),
                "istituto ospedaliero delluniversità di sassari": ("Azienda Ospedaliero Universitaria Sassari", "Sassari"),

                "university of sassari": ("University of Sassari", "Sassari"),
                "university of sassary": ("University of Sassari", "Sassari"),

                "lancianos hospital": ("Ospedale Renzetti Lanciano", "Lanciano"),

                "university hospital of parma": ("Azienda Ospedaliero-Universitaria di Parma", "Parma"),
                "parma university hospital": ("Azienda Ospedaliero-Universitaria di Parma", "Parma"),
                "azienda ospedalierouniversitaria of parma": ("Azienda Ospedaliero-Universitaria di Parma", "Parma"),
                "azienda ospedalierouniversitaria parma": ("Azienda Ospedaliero-Universitaria di Parma", "Parma"),

                "university of parma": ("University of Parma", "Parma"),
                "università di parma": ("University of Parma", "Parma"),

                "university hospital policlinico g martino": ("Azienda Ospedaliera Universitaria Gaetano Martino","Messina"),
                "university hospital of messina": ("Azienda Ospedaliera Universitaria Gaetano Martino","Messina"),
                "university hospital g martino": ("Azienda Ospedaliera Universitaria Gaetano Martino","Messina"),
                "university hospital messina": ("Azienda Ospedaliera Universitaria Gaetano Martino","Messina"),
                "g martino hospital": ("Azienda Ospedaliera Universitaria Gaetano Martino", "Messina"),
                "g martino university hospital": ("Azienda Ospedaliera Universitaria Gaetano Martino","Messina"),
                "gaetano martino university hospital": ("Azienda Ospedaliera Universitaria Gaetano Martino","Messina"),

                "papardo hospital": ("Azienda Ospedaliera Papardo","Messina"),

                "g rodolico san marco polyclinic": ("Azienda Ospedaliero Universitaria Policlinico G.Rodolico - San Marco","Messina"),

                "irccs centro neurolesi boninopulejo": ("IRCCS Centro Neurolesi Bonino Pulejo","Messina"),

                "university of messina": ("University of Messina","Messina"),

                "s maria della misericordia hospital": ("Azienda Ospedaliera Di Perugia","Perugia"),
                "santa maria misericordia hospital": ("Azienda Ospedaliera Di Perugia","Perugia"),
                "perugia general hospital": ("Azienda Ospedaliera Di Perugia","Perugia"),

                "university of perugia": ("University of Perugia","Perugia"),
                "perugia university": ("University of Perugia","Perugia"),

                "san giovanni di dio e ruggi daragona": ("Azienda Ospedaliero Universitaria San Giovanni di Dio Ruggi d'Aragona","Salerno"),

                "university of salerno": ("University of Salerno","Salerno"),

                "casa sollievo della sofferenza": ("IRCCS Ospedale Casa Sollievo della Sofferenza","San Giovanni Rotondo"),

                "policlinico riuniti di foggia": ("Azienda Ospedaliero-Universitaria Policlinico Foggia", "Foggia"),
                "foggia university hospital": ("Azienda Ospedaliero-Universitaria Policlinico Foggia", "Foggia"),
                "university hospital of foggia": ("Azienda Ospedaliero-Universitaria Policlinico Foggia", "Foggia"),

                "university of foggia": ("University of Foggia", "Foggia"),

                "university of salento": ("University of Salento", "Salento"),
                "università del salento": ("University of Salento", "Salento"),

                "policlinico universitario d casula": ("Policlinico Universitario Monserrato Duilio Casula", "Cagliari"),

                "santissima trinità asl cagliari": ("P.O. Santissima Trinità", "Cagliari"),

                "hospital armando businco cagliari": ("Ospedale Oncologico Armando Businco", "Cagliari"),

                "s michele hospital": ("Centro di Cura San Michele", "Cagliari"),

                "university of cagliari": ("University of Cagliari", "Cagliari"),
                "cagliari state university": ("University of Cagliari", "Cagliari"),

                "ss annunziata hospital": ("Presidio Ospedaliero Clinicizzato SS. Annunziata’ di Chieti", "Chieti"),
                "ss annunziata chieti hospital": ("Presidio Ospedaliero Clinicizzato SS. Annunziata’ di Chieti", "Chieti"),

                "g dannunzio university": ("Università degli Studi G. d'Annunzio Chieti–Pescara", "Chieti"),
                "university g dannunzio": ("Università degli Studi G. d'Annunzio Chieti–Pescara", "Chieti"),
                "g d annunzio university": ("Università degli Studi G. d'Annunzio Chieti–Pescara", "Chieti"),
                "gdannunzio university": ("Università degli Studi G. d'Annunzio Chieti–Pescara", "Chieti"),
                "gabriele dannunzio university": ("Università degli Studi G. d'Annunzio Chieti–Pescara", "Chieti"),
                "university of chietipescara": ("Università degli Studi G. d'Annunzio Chieti–Pescara", "Chieti"),

                "renzetti hospital": ("Ospedale Renzetti Lanciano", "Lanciano"),

                "santo spirito hospital": ("Ospedale Santo Spirito Pescara", "Pescara"),

                "policlinico san matteo": ("Ospedale Policlinico San Matteo", "Pavia"),
                "irccs san matteo": ("Ospedale Policlinico San Matteo", "Pavia"),
                "policlinico s matteo": ("Ospedale Policlinico San Matteo", "Pavia"),
                "san matteo university hospital": ("Ospedale Policlinico San Matteo", "Pavia"),
                "university hospital pavia": ("Ospedale Policlinico San Matteo", "Pavia"),

                "university of pavia": ("University of Pavia", "Pavia"),
                "pavia university": ("University of Pavia", "Pavia"),

                "asstpavia medicina interna varzi": ("Ospedale Ss.Annunziata", "Varzi"),

                "sacro cuore don calabria": ("IRCCS Sacro Cuore Don Calabria", "Negrar di Valpolicella"),
                "sacro cuoredon calabria": ("IRCCS Sacro Cuore Don Calabria", "Negrar di Valpolicella"),
                "sacrocuoredon calabria": ("IRCCS Sacro Cuore Don Calabria", "Negrar di Valpolicella"),

                "university of calabria": ("University of Calabria", "Rende"),

                "policlinico le scotte": ("Azienda Ospedaliero-Universitaria Senese", "Siena"),
                "policlinico s maria alle scotte": ("Azienda Ospedaliero-Universitaria Senese", "Siena"),
                "policlinicolescotte": ("Azienda Ospedaliero-Universitaria Senese", "Siena"),

                "ausl reggio emilia": ("Azienda Unità Sanitaria Locale IRCCS di Reggio Emilia", "Reggio Emilia"),
                "ausl di reggio emilia": ("Azienda Unità Sanitaria Locale IRCCS di Reggio Emilia", "Reggio Emilia"),
                "irccs reggio emilia": ("Azienda Unità Sanitaria Locale IRCCS di Reggio Emilia", "Reggio Emilia"),
                "auslirccs clinical cancer center of reggio emilia": ("Azienda Unità Sanitaria Locale IRCCS di Reggio Emilia", "Reggio Emilia"),

                "irccscrob": ("Centro di Riferimento Oncologico della Basilicata IRCCS", "Rionero In Vulture"),
                "irccs crob": ("Centro di Riferimento Oncologico della Basilicata IRCCS", "Rionero In Vulture"),

                "aviano cro irccs": ("Centro di Riferimento Oncologico di Aviano IRCCS", "Aviano"),
                "cro di aviano irccs": ("Centro di Riferimento Oncologico di Aviano IRCCS", "Aviano"),

                "ospedale di circolo": ("Ospedale di Circolo e Fondazione Macchi", "Varese"),
                "circolo hospital": ("Ospedale di Circolo e Fondazione Macchi", "Varese"),
                "circolo di varese hospital": ("Ospedale di Circolo e Fondazione Macchi", "Varese"),
                "asst sette laghi": ("Ospedale di Circolo e Fondazione Macchi", "Varese"),

                "university of insubria": ("University of Insubria", "Varese"),
                "universita degli studi dellinsubria": ("University of Insubria", "Varese"),
                "insubria university": ("University of Insubria", "Varese"),

                "irccs istituto romagnolo": ("IRCCS Istituto Romagnolo per lo Studio dei Tumori Dino Amadori", "Meldola"),
                "irccs romagna institute for the study of tumors dino amadori": ("IRCCS Istituto Romagnolo per lo Studio dei Tumori Dino Amadori", "Meldola"),

                "irccs burlo garofalo": ("IRCCS Materno Infantile Burlo Garofolo", "Trieste"),
                "irccs burlo garofolo": ("IRCCS Materno Infantile Burlo Garofolo", "Trieste"),

                "usl di ferrara": ("Azienda Unità Sanitaria Locale di Ferrara", "Ferrara"),

                "hospital for thalassemia and hemoglobinopathies": ("Arcispedale Sant'Anna", "Ferrara"),
                "day hospital della talassemia e delle emoglobinopatie": ("Arcispedale Sant'Anna", "Ferrara"),

                "university of ferrara": ("University of Ferrara", "Ferrara"),


            }


        for alias, (fixed_hco, fixed_city) in alias_map.items():
            alias_norm = self.normalize_hco(alias)
            if alias_norm in hco_norm:
                ans = dept_value, fixed_hco, fixed_city
                break



        return ans
    def fix_Germany(self, dept_value, hco_value, city_value,aff):
        hco_norm = self.normalize_hco(hco_value)
        aff_norm = self.normalize_hco(aff)
        city_value = city_value.lower()

        ans = dept_value, hco_value, city_value
        found = False

        university_hospital_map = {
            "aachen": ("Uniklinik RWTH Aachen", "Aachen"),
            "augsburg": ("Universitätsklinikum Augsburg", "Augsburg"),
            "bonn": ("Universitätsklinikum Bonn", "Bonn"),
            "heidelberg": ("Universitätsklinikum Heidelberg", "Heidelberg"),
            "dresden": ("Universitätsklinikum Carl Gustav Carus Dresden", "Dresden"),
            "dusseldorf": ("Universitätsklinikum Düsseldorf", "Düsseldorf"),
            "düsseldorf": ("Universitätsklinikum Düsseldorf", "Düsseldorf"),
            "erlangen": ("Universitätsklinikum Erlangen", "Erlangen"),
            "frankfurt am main": ("Universitätsklinikum Frankfurt", "Frankfurt Am Main"),
            "freiburg im breisgau": ("Universitätsklinikum Freiburg", "Freiburg"),
            "freiburg": ("Universitätsklinikum Freiburg", "Freiburg"),
            "giessen": ("Universitätsklinikum Gießen und Marburg GmbH - Standort Gießen", "Gießen"),
            "gießen": ("Universitätsklinikum Gießen und Marburg GmbH - Standort Gießen", "Gießen"),
            "göttingen": ("Universitätsmedizin Göttingen", "Göttingen"),
            "goettingen": ("Universitätsmedizin Göttingen", "Göttingen"),
            "gottingen": ("Universitätsmedizin Göttingen", "Göttingen"),
            "hanover": ("Medizinische Hochschule Hannover", "Hannover"),
            "hannover": ("Medizinische Hochschule Hannover", "Hannover"),
            "halle saale": ("Universitätsklinikum Halle (Saale)", "Halle (Saale)"),
            "halle (saale)": ("Universitätsklinikum Halle (Saale)", "Halle (Saale)"),
            "jena": ("Universitätsklinikum Jena", "Jena"),
            "kiel": ("Universitätsklinikum Schleswig-Holstein - Campus Kiel", "Kiel"),
            "lubeck": ("Universitätsklinikum Schleswig-Holstein - Campus Lübeck", "Lübeck"),
            "lübeck": ("Universitätsklinikum Schleswig-Holstein - Campus Lübeck", "Lübeck"),
            "magdeburg": ("Universitätsklinikum Magdeburg", "Magdeburg"),
            "mainz": ("Universitätsmedizin der Johannes Gutenberg-Universität Mainz", "Mainz"),
            "mannheim": ("Universitätsmedizin Mannheim", "Mannheim"),
            "marburg": ("Universitätsklinikum Gießen und Marburg GmbH - Standort Marburg", "Marburg"),
            # skipped munich because there are two lmu and tum
            "münster": ("Universitätsklinikum Münster", "Münster"),
            "munster": ("Universitätsklinikum Münster", "Münster"),
            "oldenburg": ("Klinikum Oldenburg", "Oldenburg"),
            "regensburg": ("Universitätsklinikum Regensburg", "Regensburg"),
            "rostock": ("Universitätsmedizin Rostock", "Rostock"),
            "tubingen": ("Universitätsklinikum Tübingen", "Tübingen"),
            "tübingen": ("Universitätsklinikum Tübingen", "Tübingen"),
            "ulm": ("Universitätsklinikum Ulm", "Ulm"),
            "würzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "wurzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "wuerzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
        }

        university_hospital_aliases = ["university hospital",
                                       "university medical center", "medical center university",
                                       "medical centeruniversity",
                                       "university medical centre", "medical centre university",
                                       "medical centreuniversity",
                                       "university clinic"]

        if any(x in hco_norm for x in university_hospital_aliases):
            city_key = city_value.lower().strip()

            if city_key in university_hospital_map:
                fixed_hco, fixed_city = university_hospital_map[city_key]
                ans = dept_value, fixed_hco, fixed_city
                return ans

        alias_map = {
            "charit": ("Charité - Universitätsmedizin Berlin", "Berlin"),
            "berlin institute of health": ("Charité - Universitätsmedizin Berlin", "Berlin"),
            "universitätsmedizin berlin": ("Charité - Universitätsmedizin Berlin", "Berlin"),

            "medizinische hochschule hannover": ("Medizinische Hochschule Hannover", "Hannover"),
            "hannover medical school": ("Medizinische Hochschule Hannover", "Hannover"),
            "hanover medical school": ("Medizinische Hochschule Hannover", "Hannover"),
            "medical school hannover": ("Medizinische Hochschule Hannover", "Hannover"),
            "medical school hanover": ("Medizinische Hochschule Hannover", "Hannover"),
            "hannover university school of medicine": ("Medizinische Hochschule Hannover", "Hannover"),
            "hanover university school of medicine": ("Medizinische Hochschule Hannover", "Hannover"),

            "hospital of ludwigmaximiliansuniversity": ("LMU Klinikum", "München"),
            "ludwig maximilian university hospital": ("LMU Klinikum", "München"),

            "ludwig maximilians university": ("Ludwig Maximilians University", "München"),
            "ludwig maximiliansuniversity": ("Ludwig Maximilians University", "München"),
            "ludwigmaximilians university": ("Ludwig Maximilians University", "München"),
            "ludwig maximilians universität": ("Ludwig Maximilians University", "München"),
            "ludwigmaximiliansuniversität": ("Ludwig Maximilians University", "München"),
            "dr. von hauner children's hospital": ("Ludwig Maximilians University", "München"),

            "helios klinikum berlin buch": ("HELIOS Klinikum Berlin-Buch", "Berlin"),
            "helios hospital berlin buch": ("HELIOS Klinikum Berlin-Buch", "Berlin"),

            "klinikum bielefeld mitte": ("Klinikum Bielefeld Mitte", "Bielefeld"),
            "hospital bielefeld mitte": ("Klinikum Bielefeld Mitte", "Bielefeld"),

            "robert bosch krankenhaus": ("Robert-Bosch-Krankenhaus", "Stuttgart"),
            "robert bosch hospital": ("Robert-Bosch-Krankenhaus", "Stuttgart"),

            "universitätsklinikum aachen": ("Uniklinik RWTH Aachen", "Aachen"),
            # "rwth": ("Uniklinik RWTH Aachen", "Aachen"),
            "university hospital aachen": ("Uniklinik RWTH Aachen", "Aachen"),
            # "rheinisch-westfälische technische hochschule": ("Uniklinik RWTH Aachen", "Aachen"),

            "universitätsklinikum bonn": ("Universitätsklinikum Bonn", "Bonn"),
            "university hospital bonn": ("Universitätsklinikum Bonn", "Bonn"),
            "university hospital of bonn": ("Universitätsklinikum Bonn", "Bonn"),
            "university medical center bonn ukb": ("Universitätsklinikum Bonn", "Bonn"),

            "bonn university": ("University of Bonn", "Bonn"),
            "university of bonn": ("University of Bonn", "Bonn"),

            "carl gustav carus": ("Universitätsklinikum Carl Gustav Carus Dresden", "Dresden"),
            "university hospital dresden": ("Universitätsklinikum Carl Gustav Carus Dresden", "Dresden"),

            "technische universität dresden": ("Technische Universität Dresden", "Dresden"),
            "technical university dresden": ("Technische Universität Dresden", "Dresden"),

            "universitätsklinikum der ruhr universität bochum": ("Universitätsklinikum der Ruhr-Universität Bochum",
                                                                 "Bochum"),
            "knappschaftskrankenhaus bochum": ("Universitätsklinikum der Ruhr-Universität Bochum", "Bochum"),

            "ruhruniversität bochum": ("Ruhr University Bochum", "Bochum"),
            "ruhruniversity bochum": ("Ruhr University Bochum", "Bochum"),
            "ruhr university bochum": ("Ruhr University Bochum", "Bochum"),
            "ruhr universität bochum": ("Ruhr University Bochum", "Bochum"),

            "universitätsklinikum des saarlandes": ("Universitätsklinikum des Saarlandes", "Homburg"),
            "saarland university hospital": ("Universitätsklinikum des Saarlandes", "Homburg"),

            "university of saarland": ("University of Saarland", "Saarbrücken"),
            "saarland university": ("University of Saarland", "Saarbrücken"),

            "universitätsklinikum düsseldorf": ("Universitätsklinikum Düsseldorf", "Düsseldorf"),
            "universität düsseldorf": ("Universität Düsseldorf", "Düsseldorf"),
            "university hospital düsseldorf": ("Universitätsklinikum Düsseldorf", "Düsseldorf"),
            "university hospital of düsseldorf": ("Universitätsklinikum Düsseldorf", "Düsseldorf"),
            "university hospital dusseldorf": ("Universitätsklinikum Düsseldorf", "Düsseldorf"),
            "university hospital of dusseldorf": ("Universitätsklinikum Düsseldorf", "Düsseldorf"),
            "düsseldorf university hospital": ("Universitätsklinikum Düsseldorf", "Düsseldorf"),
            "dusseldorf university hospital": ("Universitätsklinikum Düsseldorf", "Düsseldorf"),
            "heinrich heine university hospital": ("Universitätsklinikum Düsseldorf", "Düsseldorf"),
            # "heinrich heine university düsseldorf": ("Universitätsklinikum Düsseldorf", "Düsseldorf"),
            # "heinrich heine university dusseldorf": ("Universitätsklinikum Düsseldorf", "Düsseldorf"),
            # "heinrich heine universität düsseldorf": ("Universitätsklinikum Düsseldorf", "Düsseldorf"),
            # "heinrich heine universität dusseldorf": ("Universitätsklinikum Düsseldorf", "Düsseldorf"),
            # "medical faculty and university hospital düsseldorf": ("Universitätsklinikum Düsseldorf", "Düsseldorf"),

            "heinrich heine university": ("Heinrich Heine University", "Düsseldorf"),

            "evangelisches krankenhaus": ("Evangelisches Krankenhaus Düsseldorf", "Düsseldorf"),

            "universitätsklinikum erlangen": ("Universitätsklinikum Erlangen", "Erlangen"),
            "university hospital erlangen": ("Universitätsklinikum Erlangen", "Erlangen"),
            "friedrich alexander universität": ("Friedrich-Alexander-Universität Erlangen-Nürnberg", "Erlangen"),
            "friedrich alexander universitat": ("Friedrich-Alexander-Universität Erlangen-Nürnberg", "Erlangen"),
            "friedrich alexander university": ("Friedrich-Alexander-Universität Erlangen-Nürnberg", "Erlangen"),
            "university erlangen nürnberg": ("Friedrich-Alexander-Universität Erlangen-Nürnberg", "Erlangen"),
            "university of erlangen nürnberg": ("Friedrich-Alexander-Universität Erlangen-Nürnberg", "Erlangen"),
            "friedrichalexander university": ("Friedrich-Alexander-Universität Erlangen-Nürnberg", "Erlangen"),

            "universitätsklinikum essen": ("Universitätsklinikum Essen", "Essen"),
            "university hospital essen": ("Universitätsklinikum Essen", "Essen"),
            "university hospital of essen": ("Universitätsklinikum Essen", "Essen"),
            "essen university hospital": ("Universitätsklinikum Essen", "Essen"),

            "elisabeth krankenhaus essen": ("Elisabeth-Krankenhaus Essen", "Essen"),
            "elisabeth hospital essen": ("Elisabeth-Krankenhaus Essen", "Essen"),

            "ruhrlandklinik": ("Ruhrlandklinik", "Essen"),

            "universitätsklinikum frankfurt": ("Universitätsklinikum Frankfurt", "Frankfurt Am Main"),
            "university hospital frankfurt": ("Universitätsklinikum Frankfurt", "Frankfurt Am Main"),
            "frankfurt university hospital": ("Universitätsklinikum Frankfurt", "Frankfurt Am Main"),
            "frankfurt university clinic": ("Universitätsklinikum Frankfurt", "Frankfurt Am Main"),

            "goethe university frankfurt": ("Goethe University Frankfurt", "Frankfurt Am Main"),

            "universitätsklinikum freiburg": ("Universitätsklinikum Freiburg", "Freiburg"),
            "university medical center freiburg": ("Universitätsklinikum Freiburg", "Freiburg"),
            "university of freiburg medical center": ("Universitätsklinikum Freiburg", "Freiburg"),
            "medical center university of freiburg": ("Universitätsklinikum Freiburg", "Freiburg"),

            "university of freiburg": ("University of Freiburg", "Freiburg"),

            "universitätsklinikum gießen und marburg gmbh standort gießen": (
                "Universitätsklinikum Gießen und Marburg GmbH - Standort Gießen", "Gießen"),
            "university hospital giessen": ("Universitätsklinikum Gießen und Marburg GmbH - Standort Gießen", "Gießen"),
            "giessen university hospital": ("Universitätsklinikum Gießen und Marburg GmbH - Standort Gießen", "Gießen"),

            "justus liebig university": ("Justus-Liebig-Universität Gießen", "Gießen"),
            "justusliebig university": ("Justus-Liebig-Universität Gießen", "Gießen"),
            "justus liebiguniversity": ("Justus-Liebig-Universität Gießen", "Gießen"),
            "justusliebiguniversity": ("Justus-Liebig-Universität Gießen", "Gießen"),

            "universitätsklinikum gießen und marburg gmbh standort marburg": (
                "Universitätsklinikum Gießen und Marburg GmbH - Standort Marburg", "Marburg"),
            "universitätsklinikum marburg": ("Universitätsklinikum Gießen und Marburg GmbH - Standort Marburg",
                                             "Marburg"),
            "marburg university hospital": ("Universitätsklinikum Gießen und Marburg GmbH - Standort Marburg",
                                            "Marburg"),
            "university hospital marburg": ("Universitätsklinikum Gießen und Marburg GmbH - Standort Marburg",
                                            "Marburg"),

            "universitätsklinikum halle saale": ("Universitätsklinikum Halle (Saale)", "Halle (Saale)"),
            "university hospital halle": ("Universitätsklinikum Halle (Saale)", "Halle (Saale)"),
            "university clinic halle": ("Universitätsklinikum Halle (Saale)", "Halle (Saale)"),
            "hospital halle": ("Universitätsklinikum Halle (Saale)", "Halle (Saale)"),
            "university medicine halle": ("Universitätsklinikum Halle (Saale)", "Halle (Saale)"),
            "university medical center halle": ("Universitätsklinikum Halle (Saale)", "Halle (Saale)"),

            "university of halle": ("Martin-Luther-Universität Halle-Wittenberg", "Halle (Saale)"),
            "martin luther university": ("Martin-Luther-Universität Halle-Wittenberg", "Halle (Saale)"),
            "martinlutheruniversity": ("Martin-Luther-Universität Halle-Wittenberg", "Halle (Saale)"),

            "universitätsklinikum hamburg eppendorf": ("Universitätsklinikum Hamburg-Eppendorf (UKE)", "Hamburg"),
            "universitätsklinikum hamburgeppendorf": ("Universitätsklinikum Hamburg-Eppendorf (UKE)", "Hamburg"),
            "medical center hamburg eppendorf": ("Universitätsklinikum Hamburg-Eppendorf (UKE)", "Hamburg"),
            "medical centre hamburgeppendorf": ("Universitätsklinikum Hamburg-Eppendorf (UKE)", "Hamburg"),
            "university hospital hamburg": ("Universitätsklinikum Hamburg-Eppendorf (UKE)", "Hamburg"),
            "university medical center hamburgeppendorf": ("Universitätsklinikum Hamburg-Eppendorf (UKE)", "Hamburg"),
            "university medical center hamburg eppendorf": ("Universitätsklinikum Hamburg-Eppendorf (UKE)", "Hamburg"),

            "medical school hamburg": ("University of Hamburg", "Hamburg"),
            "university of hamburg": ("University of Hamburg", "Hamburg"),
            "hamburg university": ("University of Hamburg", "Hamburg"),

            "universitätsklinikum heidelberg": ("Universitätsklinikum Heidelberg", "Heidelberg"),
            "university clinic heidelberg": ("Universitätsklinikum Heidelberg", "Heidelberg"),
            "university hospital heidelberg": ("Universitätsklinikum Heidelberg", "Heidelberg"),
            "university hospital of heidelberg": ("Universitätsklinikum Heidelberg", "Heidelberg"),
            "university medical center heidelberg": ("Universitätsklinikum Heidelberg", "Heidelberg"),
            "universitätsklinik heidelberg": ("Universitätsklinikum Heidelberg", "Heidelberg"),
            "university clinic of heidelberg": ("Universitätsklinikum Heidelberg", "Heidelberg"),

            "universität heidelberg": ("University of Heidelberg", "Heidelberg"),
            "medical faculty heidelberg": ("University of Heidelberg", "Heidelberg"),
            "heidelberg university": ("University of Heidelberg", "Heidelberg"),
            "university heidelberg": ("University of Heidelberg", "Heidelberg"),
            "university of heidelberg": ("University of Heidelberg", "Heidelberg"),

            "universitätsklinikum jena": ("Universitätsklinikum Jena", "Jena"),
            "jena university hospital": ("Universitätsklinikum Jena", "Jena"),

            "universitätsklinikum köln": ("Universitätsklinikum Köln", "Köln"),
            "universitätsklinikum koln": ("Universitätsklinikum Köln", "Köln"),
            "university hospital cologne": ("Universitätsklinikum Köln", "Köln"),
            "university hospital of cologne": ("Universitätsklinikum Köln", "Köln"),
            "cologne university hospital": ("Universitätsklinikum Köln", "Köln"),
            "cologne university": ("University of Köln", "Köln"),
            "university of cologne": ("University of Köln", "Köln"),
            "köln university": ("University of Köln", "Köln"),
            "university of köln": ("University of Köln", "Köln"),

            "universitätsklinikum leipzig": ("Universitätsklinikum Leipzig", "Leipzig"),
            "university of leipzig medical centre": ("Universitätsklinikum Leipzig", "Leipzig"),
            "university hospital leipzig": ("Universitätsklinikum Leipzig", "Leipzig"),
            "university hospital of leipzig": ("Universitätsklinikum Leipzig", "Leipzig"),
            "leipzig university medical center": ("Universitätsklinikum Leipzig", "Leipzig"),
            "universität of leipzig": ("University of Leipzig", "Leipzig"),
            "university of leipzig": ("University of Leipzig", "Leipzig"),
            "leipzig university": ("University of Leipzig", "Leipzig"),

            "universitätsklinikum magdeburg": ("Universitätsklinikum Magdeburg", "Magdeburg"),
            "university hospital magdeburg": ("Universitätsklinikum Magdeburg", "Magdeburg"),

            "otto von guericke university": ("Otto von Guericke University Magdeburg", "Magdeburg"),

            "universitätsklinikum münster": ("Universitätsklinikum Münster", "Münster"),
            "universitätsklinikum munster": ("Universitätsklinikum Münster", "Münster"),
            "university hospital münster": ("Universitätsklinikum Münster", "Münster"),
            "university hospital munster": ("Universitätsklinikum Münster", "Münster"),
            "university medical center münster": ("Universitätsklinikum Münster", "Münster"),
            "university medical center munster": ("Universitätsklinikum Münster", "Münster"),
            "university children's hospital münster": ("Universitätsklinikum Münster", "Münster"),
            "children's hospital münster": ("Universitätsklinikum Münster", "Münster"),
            "kinderklinik münster": ("Universitätsklinikum Münster", "Münster"),

            "university münster": ("University of Münster", "Münster"),
            "münster university": ("University of Münster", "Münster"),
            "university of münster": ("University of Münster", "Münster"),
            "university munster": ("University of Münster", "Münster"),
            "munster university": ("University of Münster", "Münster"),
            "university of munster": ("University of Münster", "Münster"),

            "universitätsklinikum regensburg": ("Universitätsklinikum Regensburg", "Regensburg"),
            "university hospital regensburg": ("Universitätsklinikum Regensburg", "Regensburg"),
            "university medical center regensburg": ("Universitätsklinikum Regensburg", "Regensburg"),

            "university of regensburg": ("University of Regensburg", "Regensburg"),
            "regensburg university": ("University of Regensburg", "Regensburg"),
            "university regensburg": ("University of Regensburg", "Regensburg"),

            "universitätsklinikum schleswig holstein campus kiel": (
                "Universitätsklinikum Schleswig-Holstein - Campus Kiel", "Kiel"),
            "university medical centre schleswig holstein and kiel university": (
                "Universitätsklinikum Schleswig-Holstein - Campus Kiel", "Kiel"),
            "university hospital shleswig holstein campus kiel": (
                "Universitätsklinikum Schleswig-Holstein - Campus Kiel", "Kiel"),
            "university hospital schleswig holstein campus kiel": (
                "Universitätsklinikum Schleswig-Holstein - Campus Kiel", "Kiel"),

            "christianalbrechtsuniversität zu kiel": ("University of Kiel", "Kiel"),
            "kiel university": ("University of Kiel", "Kiel"),

            "universitätsklinikum schleswig holstein campus lübeck": (
                "Universitätsklinikum Schleswig-Holstein - Campus Lübeck", "Lübeck"),
            "universitätsklinikum schleswig holstein campus lubeck": (
                "Universitätsklinikum Schleswig-Holstein - Campus Lübeck", "Lübeck"),
            "university medical centre schleswig holstein and lübeck university": (
                "Universitätsklinikum Schleswig-Holstein - Campus Lübeck", "Lübeck"),
            "university medical centre schleswig holstein and lubeck university": (
                "Universitätsklinikum Schleswig-Holstein - Campus Lübeck", "Lübeck"),
            "university hospital shleswig holstein campus lübeck": (
                "Universitätsklinikum Schleswig-Holstein - Campus Lübeck", "Lübeck"),
            "university hospital shleswig holstein campus lubeck": (
                "Universitätsklinikum Schleswig-Holstein - Campus Lübeck", "Lübeck"),
            "university hospital schleswig holstein campus lübeck": (
                "Universitätsklinikum Schleswig-Holstein - Campus Lübeck", "Lübeck"),
            "university hospital schleswig holstein campus lubeck": (
                "Universitätsklinikum Schleswig-Holstein - Campus Lübeck", "Lübeck"),

            "universitätsklinikum tübingen": ("Universitätsklinikum Tübingen", "Tübingen"),
            "universitätsklinikum tubingen": ("Universitätsklinikum Tübingen", "Tübingen"),
            "tübingen university hospital": ("Universitätsklinikum Tübingen", "Tübingen"),
            "university hospital tübingen": ("Universitätsklinikum Tübingen", "Tübingen"),
            "university hospital tubingen": ("Universitätsklinikum Tübingen", "Tübingen"),

            "eberhard karls university": ("Eberhard Karls University of Tübingen", "Tübingen"),
            "karls eberhards universität": ("Eberhard Karls University of Tübingen", "Tübingen"),
            "university of tübingen": ("Eberhard Karls University of Tübingen", "Tübingen"),
            "university of tubingen": ("Eberhard Karls University of Tübingen", "Tübingen"),
            "tübingen university": ("Eberhard Karls University of Tübingen", "Tübingen"),
            "tubingen university": ("Eberhard Karls University of Tübingen", "Tübingen"),

            "universitätsklinikum ulm": ("Universitätsklinikum Ulm", "Ulm"),
            "university clinic ulm": ("Universitätsklinikum Ulm", "Ulm"),
            "ulm university hospital": ("Universitätsklinikum Ulm", "Ulm"),
            "university hospital ulm": ("Universitätsklinikum Ulm", "Ulm"),
            "university medical center ulm": ("Universitätsklinikum Ulm", "Ulm"),

            "ulm university": ("University of Ulm", "Ulm"),
            "university of ulm": ("University of Ulm", "Ulm"),

            "bundeswehrkrankenhaus ulm": ("Bundeswehrkrankenhaus Ulm", "Ulm"),
            "german armed forces hospital ulm": ("Bundeswehrkrankenhaus Ulm", "Ulm"),

            "technical university dortmund": ("Technische Universität Dortmund", "Dortmund"),

            "universitätsklinikum würzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "universitätsklinikum wurzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "university hospital of würzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "university hospital of wurzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "university hospital of wuerzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "university hospital in würzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "university hospital in wurzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "university hospital in wuerzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "university hospital würzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "university hospital wurzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "university hospital wuerzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "university hospitals of würzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "university hospitals of wurzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "university hospitals of wuerzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "university hospitals in würzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "university hospitals in wurzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "university hospitals in wuerzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "university hospitals würzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "university hospitals wurzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "julius maximilians university hospital würzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "julius maximilians university hospital wurzburg": ("Universitätsklinikum Würzburg", "Würzburg"),
            "julius maximilians university hospital wuerzburg": ("Universitätsklinikum Würzburg", "Würzburg"),

            "würzburg university": ("University of Würzburg", "Würzburg"),
            "wurzburg university": ("University of Würzburg", "Würzburg"),
            "wuerzburg university": ("University of Würzburg", "Würzburg"),
            "university of würzburg": ("University of Würzburg", "Würzburg"),
            "university of wurzburg": ("University of Würzburg", "Würzburg"),
            "university of wuerzbur": ("University of Würzburg", "Würzburg"),

            "university hospital mainz": ("Universitätsmedizin der Johannes Gutenberg-Universität Mainz", "Mainz"),
            "university medical center mainz": ("Universitätsmedizin der Johannes Gutenberg-Universität Mainz",
                                                "Mainz"),
            "university of mainz medical center": ("Universitätsmedizin der Johannes Gutenberg-Universität Mainz",
                                                   "Mainz"),

            "johannes gutenberg universität": ("Johannes Gutenberg University Mainz", "Mainz"),
            "johannes gutenberg university": ("Johannes Gutenberg University Mainz", "Mainz"),

            "universitätsmedizin göttingen": ("Universitätsmedizin Göttingen", "Göttingen"),
            "universitätsmedizin gottingen": ("Universitätsmedizin Göttingen", "Göttingen"),
            "universitätsmedizin goettingen": ("Universitätsmedizin Göttingen", "Göttingen"),
            "universitätsklinikum göttingen": ("Universitätsmedizin Göttingen", "Göttingen"),
            "universitätsklinikum gottingen": ("Universitätsmedizin Göttingen", "Göttingen"),
            "universitätsklinikum goettingen": ("Universitätsmedizin Göttingen", "Göttingen"),
            "university medical center göttingen": ("Universitätsmedizin Göttingen", "Göttingen"),
            "university medical center goettingen": ("Universitätsmedizin Göttingen", "Göttingen"),
            "university medical center gottingen": ("Universitätsmedizin Göttingen", "Göttingen"),

            "university of gottingen": ("University of Göttingen", "Göttingen"),
            "gottingen university": ("University of Göttingen", "Göttingen"),
            "university of goettingen": ("University of Göttingen", "Göttingen"),
            "goettingen university": ("University of Göttingen", "Göttingen"),
            "university of göttingen": ("University of Göttingen", "Göttingen"),
            "göttingen university": ("University of Göttingen", "Göttingen"),
            "university medicine goettingen": ("University of Göttingen", "Göttingen"),

            "universitätsmedizin greifswald": ("Universitätsmedizin Greifswald", "Greifswald"),
            "university medicine greifswald": ("Universitätsmedizin Greifswald", "Greifswald"),
            "university hospital greifswald": ("Universitätsmedizin Greifswald", "Greifswald"),
            "greifswald university medical center": ("Universitätsmedizin Greifswald", "Greifswald"),

            "university greifswald": ("University of Greifswald", "Greifswald"),

            "universitätsmedizin mannheim": ("Universitätsmedizin Mannheim", "Mannheim"),
            "university hospital mannheim": ("Universitätsmedizin Mannheim", "Mannheim"),
            "university medical center mannheim": ("Universitätsmedizin Mannheim", "Mannheim"),
            "university medical centre mannheim": ("Universitätsmedizin Mannheim", "Mannheim"),
            "medical faculty mannheim": ("Universitätsmedizin Mannheim", "Mannheim"),

            "universitätsmedizin rostock": ("Universitätsmedizin Rostock", "Rostock"),
            "rostock university medical center": ("Universitätsmedizin Rostock", "Rostock"),
            "university medicine rostock": ("Universitätsmedizin Rostock", "Rostock"),

            "university of rostock": ("University of Rostock", "Rostock"),
            "rostock university": ("University of Rostock", "Rostock"),

            "heinrich heine universität düsseldorf": ("Heinrich-Heine-Universität Düsseldorf", "Düsseldorf"),
            "heinrich heine universität dusseldorf": ("Heinrich-Heine-Universität Düsseldorf", "Düsseldorf"),
            "heinrich heine university düsseldorf": ("Heinrich-Heine-Universität Düsseldorf", "Düsseldorf"),
            "heinrich heine university dusseldorf": ("Heinrich-Heine-Universität Düsseldorf", "Düsseldorf"),

            "rechts der isar": ("TUM Klinikum Rechts der Isar", "München"),
            "technical university of munich hospital": ("TUM Klinikum Rechts der Isar", "München"),
            "technical university munich hospital": ("TUM Klinikum Rechts der Isar", "München"),
            "technische universität münchen hospital": ("TUM Klinikum Rechts der Isar", "München"),
            "technische universität munchen hospital": ("TUM Klinikum Rechts der Isar", "München"),
            "tum university hospital": ("TUM Klinikum Rechts der Isar", "München"),
            "hospital of the university of munich": ("TUM Klinikum Rechts der Isar", "München"),

            "tu munich": ("Technische Universität München", "München"),
            "tu münchen": ("Technische Universität München", "München"),
            "tu munchen": ("Technische Universität München", "München"),
            "technical university of munich": ("Technische Universität München", "München"),
            "technical university munich": ("Technische Universität München", "München"),
            "technische universität münchen": ("Technische Universität München", "München"),
            "technische universität munchen": ("Technische Universität München", "München"),
            "tum school of medicine": ("Technische Universität München", "München"),

            "universitätsklinikum augsburg": ("Universitätsklinikum Augsburg", "Augsburg"),
            "university hospital augsburg": ("Universitätsklinikum Augsburg", "Augsburg"),
            "university hospital of augsburg": ("Universitätsklinikum Augsburg", "Augsburg"),
            "augsburg university hospital": ("Universitätsklinikum Augsburg", "Augsburg"),

            "sana klinikum offenbach": ("Sana Klinikum Offenbach", "Offenbach"),
            "sana hospital offenbach": ("Sana Klinikum Offenbach", "Offenbach"),

            "asklepios klinik altona": ("Asklepios Klinik Altona", "Hamburg"),
            "asklepios clinic altona": ("Asklepios Klinik Altona", "Hamburg"),

            "hospital fürth": ("Klinikum Fürth", "Fürth"),
            "hospital furth": ("Klinikum Fürth", "Fürth"),

            # "german cancer research center": ("German Cancer Research Center", "Heidelberg"),

            "philipps university marburg": ("Philipps University Marburg", "Marburg"),
            "philipps universität marburg": ("Philipps University Marburg", "Marburg"),
            "philipps university": ("Philipps University Marburg", "Marburg"),

            "robert bosch center for tumor diseases": ("Robert Bosch Center for Tumor Diseases", "Stuttgart"),

            "university of hohenheim": ("University of Hohenheim", "Stuttgart"),
            "hohenheim university": ("University of Hohenheim", "Stuttgart"),
            "hohenheim universität": ("University of Hohenheim", "Stuttgart"),

            "johannes wesling university hospital": ("Johannes Wesling Klinikum Minden", "Minden"),

            "clinical center osnabrück": ("Klinikum Osnabrück GmbH", "Osnabrück"),

            "university hospital brandenburg": ("Universitätsklinikum Brandenburg an der Havel GmbH",
                                                "Brandenburg an der Havel"),
            "university hospital of the brandenburg": ("Universitätsklinikum Brandenburg an der Havel GmbH",
                                                       "Brandenburg an der Havel"),
            "university hospital of brandenburg": ("Universitätsklinikum Brandenburg an der Havel GmbH",
                                                   "Brandenburg an der Havel"),

            "university hospital oldenburg": ("Klinikum Oldenburg", "Oldenburg"),

            "university of bayreuth": ("University of Bayreuth", "Bayreuth"),
            "universität bayreuth": ("University of Bayreuth", "Bayreuth"),

            "university of konstanz": ("University of Konstanz", "Konstanz"),

        }

        for alias, (fixed_hco, fixed_city) in alias_map.items():
            if alias in hco_norm:
                ans = dept_value, fixed_hco, fixed_city

                if fixed_hco == "University of Bonn" and "hospital" in aff_norm:
                    ans = dept_value, "Universitätsklinikum Bonn", fixed_city

                if fixed_hco == "University of Ulm" and "hospital" in aff_norm:
                    ans = dept_value, "Universitätsklinikum Ulm", fixed_city

                if fixed_hco == "University of Köln" and "hospital" in aff_norm:
                    ans = dept_value, "Universitätsklinikum Köln", fixed_city

                if fixed_hco == "University of Freiburg" and "hospital" in aff_norm:
                    ans = dept_value, "Universitätsklinikum Freiburg", fixed_city

                if fixed_hco == "Ludwig Maximilians University" and "hospital" in aff_norm:
                    ans = dept_value, "LMU Klinikum", fixed_city
                found = True
                break

        # if hco_norm == "university":
        #     ans = dept_value, "", city_value.title()

        if hco_norm == "boehringer ingelheim pharma":
            ans = dept_value, "Boehringer Ingelheim Pharma GmbH & Co. KG", city_value.title()

        if "university hospital schleswig holstein" in hco_norm or "university medical center schleswig holstein" in hco_norm or "university medical centre schleswig holstein" in hco_norm:
            if "kiel" in hco_norm or "kiel" in city_value.lower():
                ans = dept_value, "Universitätsklinikum Schleswig-Holstein - Campus Kiel", "Kiel"

            elif "lubeck" in hco_norm or "lubeck" in city_value.lower() or "lübeck" in hco_norm or "lübeck" in city_value.lower():
                ans = dept_value, "Universitätsklinikum Schleswig-Holstein - Campus Lübeck", "Lübeck"

            else:
                if "kiel" in aff_norm:
                    ans = dept_value, "Universitätsklinikum Schleswig-Holstein - Campus Kiel", "Kiel"
                elif "lubeck" in aff_norm:
                    ans = dept_value, "Universitätsklinikum Schleswig-Holstein - Campus Lübeck", "Lübeck"
                else:
                    ans = dept_value, "Universitätsklinikum Schleswig-Holstein", city_value.title()

        if "school of medicine and health" in hco_norm and (
                "munich" in city_value.lower() or "münchen" in city_value.lower()):
            ans = dept_value, "TUM Klinikum Rechts der Isar", "München"

        if "medical clinic and polyclinic ii" in hco_norm and (
                "munich" in city_value.lower() or "münchen" in city_value.lower()):
            ans = "Medical Clinic and Polyclinic II", "LMU Klinikum", "München"

        if "university hospital of giessen and marburg" in hco_norm or "universitätsklinikum gießen und marburg" in hco_norm or "universitätsklinikum giessen und marburg" in hco_norm or "university hospital of giessen" in hco_norm:
            if "marburg" in city_value.lower():
                ans = dept_value, "Universitätsklinikum Gießen und Marburg GmbH - Standort Marburg", "Marburg"
            elif "giessen" in city_value or "gießen" in city_value.lower():
                ans = dept_value, "Universitätsklinikum Gießen und Marburg GmbH - Standort Gießen", "Gießen"
            else:
                ans = dept_value, "Universitätsklinikum Gießen und Marburg GmbH", city_value.title()

        if (
                "st. josef hospital" in hco_norm or "st josef hospital" in hco_norm or "st josefhospital" in hco_norm or "sankt josef hospital" in hco_norm):
            if "bochum" in city_value.lower():
                ans = dept_value, "St. Josef-Hospital - Bochum", "Bochum"
            else:
                ans = dept_value, f"St. Josef-Hospital - {city_value.title()}", city_value.title()

        if ("hamburg eppendorf" in aff_norm or "hamburgeppendorf" in aff_norm) and (
                "hospital" in aff or "university medical" in aff_norm):
            ans = dept_value, "Universitätsklinikum Hamburg-Eppendorf (UKE)", "Hamburg"

        if "university cancer center hamburg" in hco_norm:
            ans = "Cancer center", "Universitätsklinikum Hamburg-Eppendorf (UKE)", "Hamburg"

        if "knappschaftskrankenhaus" in hco_norm and "bochum" in city_value.lower():
            ans = dept_value, "Universitätsklinikum der Ruhr-Universität Bochum", "Bochum"

        if (
                "rwth" in hco_norm and "hospital" in aff_norm) or "rheinisch-westfälische technische hochschule" in hco_norm:
            ans = dept_value, "Uniklinik RWTH Aachen", "Aachen"

        if "LMU" in aff:
            ans = dept_value, "LMU Klinikum", "München"

        if "technical university" in hco_norm and any(
                k in city_value.lower() for k in ["munich", "munchen", "münchen"]):
            ans = dept_value, "Technische Universität München", "München"

        # if "cancer research" in aff_norm and not found:
        if any(k in aff_norm for k in ["cancer research", "dkfz", "dktk", "bzkf"]) and not found:
            hco_name = []
            if "dkfz" in aff_norm or "german cancer research center" in aff_norm:
                hco_name.append("German Cancer Research Center (DKFZ)")
            if "dktk" in aff_norm or "german cancer consortium" in aff_norm:
                hco_name.append("German Cancer Consortium (DKTK)")
            if "bzkf" in aff_norm or "bavarian cancer research center" in aff_norm:
                hco_name.append("Bavarian Cancer Research Center (BZKF)")
            if len(hco_name) > 0:
                ans = "", ", ".join(hco_name), city_value.title()

        # if hco_norm == "German Center for Lung Research (DZL)"
        if "german center for lung research" in aff_norm and "and" not in aff_norm:
            fixed_hco = "German Center for Lung Research (DZL)"
            if city_value:
                fixed_hco += f" - {city_value.title()}"
            ans = dept_value, fixed_hco, city_value.title()
        return ans

    def fix_France(self,dept_value,hco_value, city_value,aff):
        hco_norm = self.normalize_hco(hco_value)
        aff_norm = self.normalize_hco(aff)
        city_key = city_value.lower().strip().replace("-", " ")
        city_key = re.sub(r"\bcedex\b.*$", "", city_key).strip()

        ans = dept_value, hco_value, city_value

        if "chuva" in aff_norm:
            return dept_value, hco_value, city_value

        university_hospital_map = {
            "amiens": ("CHU Amiens-Picardie", "Amiens"),
            "angers": ("CHU d'Angers", "Angers"),
            "besançon": ("CHU de Besançon", "Besançon"),
            "besancon": ("CHU de Besançon", "Besançon"),
            "bordeaux": ("CHU de Bordeaux", "Bordeaux"),
            "brest": ("CHU de Brest", "Brest"),
            "caen": ("CHU de Caen Normandie", "Caen"),
            "clermont ferrand": ("CHU de Clermont-Ferrand", "Clermont-Ferrand"),
            "dijon": ("CHU Dijon Bourgogne", "Dijon"),
            "grenoble": ("CHU Grenoble Alpes", "Grenoble"),
            "lille": ("CHU de Lille", "Lille"),
            "limoges": ("CHU de Limoges", "Limoges"),
            "lyon": ("Hospices Civils de Lyon", "Lyon"),
            "marseille": ("Assistance Publique - Hôpitaux de Marseille", "Marseille"),
            "montpellier": ("CHU de Montpellier", "Montpellier"),
            "nancy": ("CHRU de Nancy", "Nancy"),
            "nantes": ("CHU de Nantes", "Nantes"),
            "nice": ("CHU de Nice", "Nice"),
            "nîmes": ("CHU de Nîmes", "Nîmes"),
            "nimes": ("CHU de Nîmes", "Nîmes"),
            "paris": ("Assistance Publique - Hôpitaux de Paris", "Paris"),
            "poitiers": ("CHU de Poitiers", "Poitiers"),
            "reims": ("CHU de Reims", "Reims"),
            "rennes": ("CHU de Rennes", "Rennes"),
            "rouen": ("CHU de Rouen", "Rouen"),
            "saint etienne": ("CHU de Saint-Étienne", "Saint-Étienne"),
            "saint-étienne": ("CHU de Saint-Étienne", "Saint-Étienne"),
            "saintetienne": ("CHU de Saint-Étienne", "Saint-Étienne"),
            "strasbourg": ("Hôpitaux Universitaires de Strasbourg", "Strasbourg"),
            "toulouse": ("CHU de Toulouse", "Toulouse"),
            "tours": ("CHRU de Tours", "Tours"),
        }

        generic_hospital_terms = [
            "university hospital",
            "university hospitals",
            "university medical center",
            "university medical centre",
            "centre hospitalier universitaire",
            "centre hospitalier regional universitaire",
            "centre hospitalier régional universitaire",
            "chu",
            "chru",
        ]

        if any(term in hco_norm for term in generic_hospital_terms):
            if city_key in university_hospital_map:
                fixed_hco, fixed_city = university_hospital_map[city_key]
                return dept_value, fixed_hco, fixed_city

            if len(city_key.split()) > 1:
                for city in city_key.split():
                    if city in university_hospital_map:
                        fixed_hco, fixed_city = university_hospital_map[city]
                        return dept_value, fixed_hco, fixed_city

        if hco_norm in {"chu", "chru", "university hospital", "centre hospitalier universitaire"}:
            if city_key in university_hospital_map:
                fixed_hco, fixed_city = university_hospital_map[city_key]
                ans = dept_value, fixed_hco, fixed_city

        # Paris AP-HP hospital-specific disambiguation from full affiliation text
        aphp_aliases = ["ap hp", "aphp", "assistance publique hopitaux paris",
                        "assistance publique hopitaux de paris", "assistance publique paris"]
        if any([term in aff_norm for term in aphp_aliases]):
            aphp_hospital_map = {
                "albert chenevier": ("Hôpital Albert-Chenevier", "Créteil"),
                "ambroise pare": ("Hôpital Ambroise-Paré", "Boulogne-Billancourt"),
                "ambroise paré": ("Hôpital Ambroise-Paré", "Boulogne-Billancourt"),
                "antoine beclere": ("Hôpital Antoine-Béclère", "Clamart"),
                "antoine béclère": ("Hôpital Antoine-Béclère", "Clamart"),
                "armand trousseau": ("Hôpital Armand-Trousseau", "Paris"),
                "trousseau": ("Hôpital Armand-Trousseau", "Paris"),
                "avicenne": ("Hôpital Avicenne", "Bobigny"),
                "beaujon": ("Hôpital Beaujon", "Clichy"),
                "berck": ("Hôpital maritime de Berck", "Berck-sur-Mer"),
                "bicetre": ("Hôpital Bicêtre", "Le Kremlin-Bicêtre"),
                "bicêtre": ("Hôpital Bicêtre", "Le Kremlin-Bicêtre"),
                "bichat": ("Hôpital Bichat - Claude-Bernard", "Paris"),
                "claude bernard": ("Hôpital Bichat - Claude-Bernard", "Paris"),
                "bretonneau": ("Hôpital Bretonneau", "Paris"),
                "broca": ("Hôpital Broca - La Collégiale", "Paris"),
                "la collegiale": ("Hôpital Broca - La Collégiale", "Paris"),
                "la collégiale": ("Hôpital Broca - La Collégiale", "Paris"),
                "charles foix": ("Hôpital Charles-Foix", "Ivry-sur-Seine"),
                "cochin": ("Hôpital Cochin - Port-Royal", "Paris"),
                "port royal": ("Hôpital Cochin - Port-Royal", "Paris"),
                "corentin celton": ("Hôpital Corentin-Celton", "Issy-les-Moulineaux"),
                "dupuytren": ("Hôpital Dupuytren", "Draveil"),
                "emile roux": ("Hôpital Emile-Roux", "Limeil-Brévannes"),
                "fernand widal": ("Hôpital Fernand-Widal", "Paris"),
                "georges clemenceau": ("Hôpital Georges-Clemenceau", "Champcueil"),
                "hendaye": ("Hôpital marin de Hendaye", "Hendaye"),
                "henri mondor": ("Hôpital Henri-Mondor", "Créteil"),
                "georges pompidou": ("Hôpital européen Georges-Pompidou", "Paris"),
                "hegp": ("Hôpital européen Georges-Pompidou", "Paris"),
                "hotel dieu": ("Hôpital Hôtel-Dieu", "Paris"),
                "hôtel dieu": ("Hôpital Hôtel-Dieu", "Paris"),
                "jean verdier": ("Hôpital Jean-Verdier", "Bondy"),
                "la roche guyon": ("Hôpital La Roche-Guyon", "La Roche-Guyon"),
                "lariboisiere": ("Hôpital Lariboisière", "Paris"),
                "lariboisière": ("Hôpital Lariboisière", "Paris"),
                "louis mourier": ("Hôpital Louis-Mourier", "Colombes"),
                "necker": ("Hôpital Necker-Enfants malades", "Paris"),
                "paul brousse": ("Hôpital Paul-Brousse", "Villejuif"),
                "paul doumer": ("Hôpital Paul-Doumer", "Labruyère"),
                "pitie": ("Hôpital Pitié-Salpêtrière", "Paris"),
                "pitié": ("Hôpital Pitié-Salpêtrière", "Paris"),
                "salpetriere": ("Hôpital Pitié-Salpêtrière", "Paris"),
                "salpêtrière": ("Hôpital Pitié-Salpêtrière", "Paris"),
                "raymond poincare": ("Hôpital Raymond-Poincaré", "Garches"),
                "raymond poincaré": ("Hôpital Raymond-Poincaré", "Garches"),
                "rene muret": ("Hôpital René-Muret", "Sevran"),
                "rené muret": ("Hôpital René-Muret", "Sevran"),
                "robert debre": ("Hôpital Robert-Debré", "Paris"),
                "robert debré": ("Hôpital Robert-Debré", "Paris"),
                "rothschild": ("Hôpital Rothschild", "Paris"),
                "saint antoine": ("Hôpital Saint-Antoine", "Paris"),
                "saint louis": ("Hôpital Saint-Louis", "Paris"),
                "sainte perine": ("Hôpital Sainte-Périne", "Paris"),
                "sainte périne": ("Hôpital Sainte-Périne", "Paris"),
                "san salvadour": ("Hôpital San Salvadour", "Hyères"),
                "tenon": ("Hôpital Tenon", "Paris"),
                "vaugirard": ("Hôpital Vaugirard - Gabriel-Pallez", "Paris"),
                "gabriel pallez": ("Hôpital Vaugirard - Gabriel-Pallez", "Paris"),
            }

            for alias, (fixed_hco, fixed_city) in aphp_hospital_map.items():
                alias_norm = self.normalize_hco(alias)
                if alias_norm in aff_norm:
                    ans = dept_value, fixed_hco, fixed_city
                    return ans
            else:
                ans = dept_value, "Assistance Publique - Hôpitaux de Paris", "Paris"

        # Marseille AP-HM hospital-specific disambiguation from full affiliation text
        aphm_aliases = ["ap hm", "aphm", "assistance publique hopitaux marseille",
                        "assistance publique hopitaux de marseille", "assistance publique marseille"]
        if any([term in aff_norm for term in aphm_aliases]):
            aphm_hospital_map = {
                "la timone": ("Hôpital de la Timone", "Marseille"),
                "timone": ("Hôpital de la Timone", "Marseille"),

                "hopital nord": ("Hôpital Nord", "Marseille"),
                "hôpital nord": ("Hôpital Nord", "Marseille"),
                "nord": ("Hôpital Nord", "Marseille"),

                "la conception": ("Hôpital de la Conception", "Marseille"),
                "conception": ("Hôpital de la Conception", "Marseille"),

                "sainte marguerite": ("Hôpital Sainte-Marguerite", "Marseille"),
                "ste marguerite": ("Hôpital Sainte-Marguerite", "Marseille"),

                "salvator": ("Hôpital Salvator", "Marseille"),

                "adultes de la timone": ("Hôpital de la Timone", "Marseille"),
                "enfants de la timone": ("Hôpital de la Timone", "Marseille"),
                "timone enfants": ("Hôpital de la Timone", "Marseille"),

                "hopital sud": ("Hôpital Sainte-Marguerite", "Marseille"),
                "hôpital sud": ("Hôpital Sainte-Marguerite", "Marseille"),
            }

            for alias, (fixed_hco, fixed_city) in aphm_hospital_map.items():
                alias_norm = self.normalize_hco(alias)
                if alias_norm in aff_norm:
                    ans = dept_value, fixed_hco, fixed_city
                    return ans
            else:
                ans = dept_value, "Assistance Publique - Hôpitaux de Marseille", "Marseille"

        alias_map = {
            # AP-HP
            "albert chenevier": ("Hôpital Albert-Chenevier", "Créteil"),
            "ambroise pare": ("Hôpital Ambroise-Paré", "Boulogne-Billancourt"),
            "ambroise paré": ("Hôpital Ambroise-Paré", "Boulogne-Billancourt"),
            "antoine beclere": ("Hôpital Antoine-Béclère", "Clamart"),
            "antoine béclère": ("Hôpital Antoine-Béclère", "Clamart"),
            "armand trousseau": ("Hôpital Armand-Trousseau", "Paris"),
            "avicenne": ("Hôpital Avicenne", "Bobigny"),
            "beaujon": ("Hôpital Beaujon", "Clichy"),
            "bicetre": ("Hôpital Bicêtre", "Le Kremlin-Bicêtre"),
            "bicêtre": ("Hôpital Bicêtre", "Le Kremlin-Bicêtre"),
            "bichat": ("Hôpital Bichat - Claude-Bernard", "Paris"),
            "bretonneau": ("Hôpital Bretonneau", "Paris"),
            "broca": ("Hôpital Broca - La Collégiale", "Paris"),
            "charles foix": ("Hôpital Charles-Foix", "Ivry-sur-Seine"),
            "cochin": ("Hôpital Cochin - Port-Royal", "Paris"),
            "corentin celton": ("Hôpital Corentin-Celton", "Issy-les-Moulineaux"),
            "emile roux": ("Hôpital Emile-Roux", "Limeil-Brévannes"),
            "fernand widal": ("Hôpital Fernand-Widal", "Paris"),
            "georges clemenceau": ("Hôpital Georges-Clemenceau", "Champcueil"),
            "henri mondor": ("Hôpital Henri-Mondor", "Créteil"),
            "georges pompidou": ("Hôpital européen Georges-Pompidou", "Paris"),
            "hegp": ("Hôpital européen Georges-Pompidou", "Paris"),
            "jean verdier": ("Hôpital Jean-Verdier", "Bondy"),
            "la roche guyon": ("Hôpital La Roche-Guyon", "La Roche-Guyon"),
            "lariboisiere": ("Hôpital Lariboisière", "Paris"),
            "lariboisière": ("Hôpital Lariboisière", "Paris"),
            "louis mourier": ("Hôpital Louis-Mourier", "Colombes"),
            "paul brousse": ("Hôpital Paul-Brousse", "Villejuif"),
            "paul doumer": ("Hôpital Paul-Doumer", "Labruyère"),
            "raymond poincare": ("Hôpital Raymond-Poincaré", "Garches"),
            "raymond poincaré": ("Hôpital Raymond-Poincaré", "Garches"),
            "rene muret": ("Hôpital René-Muret", "Sevran"),
            "rené muret": ("Hôpital René-Muret", "Sevran"),
            "robert debre": ("Hôpital Robert-Debré", "Paris"),
            "robert debré": ("Hôpital Robert-Debré", "Paris"),
            "rothschild": ("Hôpital Rothschild", "Paris"),
            "sainte perine": ("Hôpital Sainte-Périne", "Paris"),
            "sainte périne": ("Hôpital Sainte-Périne", "Paris"),
            "san salvadour": ("Hôpital San Salvadour", "Hyères"),
            "tenon": ("Hôpital Tenon", "Paris"),
            "vaugirard": ("Hôpital Vaugirard - Gabriel-Pallez", "Paris"),
            "gabriel pallez": ("Hôpital Vaugirard - Gabriel-Pallez", "Paris"),

            # AP-HM
            "la timone": ("Hôpital de la Timone", "Marseille"),
            "timone": ("Hôpital de la Timone", "Marseille"),
            "adultes de la timone": ("Hôpital de la Timone", "Marseille"),
            "enfants de la timone": ("Hôpital de la Timone", "Marseille"),
            "timone enfants": ("Hôpital de la Timone", "Marseille"),

            # CHU Bordeaux - site level
            "pellegrin": ("Hôpital Pellegrin - CHU de Bordeaux", "Bordeaux"),
            "hopital pellegrin": ("Hôpital Pellegrin - CHU de Bordeaux", "Bordeaux"),
            "hôpital pellegrin": ("Hôpital Pellegrin - CHU de Bordeaux", "Bordeaux"),
            "chu pellegrin": ("Hôpital Pellegrin - CHU de Bordeaux", "Bordeaux"),

            "saint andre bordeaux": ("Hôpital Saint-André - CHU de Bordeaux", "Bordeaux"),
            "saint-andre bordeaux": ("Hôpital Saint-André - CHU de Bordeaux", "Bordeaux"),
            "saint-andré bordeaux": ("Hôpital Saint-André - CHU de Bordeaux", "Bordeaux"),
            "hopital saint andre bordeaux": ("Hôpital Saint-André - CHU de Bordeaux", "Bordeaux"),
            "hôpital saint-andré bordeaux": ("Hôpital Saint-André - CHU de Bordeaux", "Bordeaux"),

            "haut leveque": ("Hôpital Haut-Lévêque - CHU de Bordeaux", "Pessac"),
            "haut-lévêque": ("Hôpital Haut-Lévêque - CHU de Bordeaux", "Pessac"),
            "haut leveque hospital": ("Hôpital Haut-Lévêque - CHU de Bordeaux", "Pessac"),

            "xavier arnozan": ("Hôpital Xavier-Arnozan - CHU de Bordeaux", "Pessac"),

            # CHU Toulouse - site level
            "purpan": ("Hôpital Purpan - CHU de Toulouse", "Toulouse"),
            "hopital purpan": ("Hôpital Purpan - CHU de Toulouse", "Toulouse"),
            "hôpital purpan": ("Hôpital Purpan - CHU de Toulouse", "Toulouse"),

            "rangueil": ("Hôpital Rangueil - CHU de Toulouse", "Toulouse"),
            "hopital rangueil": ("Hôpital Rangueil - CHU de Toulouse", "Toulouse"),
            "hôpital rangueil": ("Hôpital Rangueil - CHU de Toulouse", "Toulouse"),

            "larrey": ("Hôpital Larrey - CHU de Toulouse", "Toulouse"),
            "hopital larrey": ("Hôpital Larrey - CHU de Toulouse", "Toulouse"),
            "hôpital larrey": ("Hôpital Larrey - CHU de Toulouse", "Toulouse"),

            "paule de viguier": ("Hôpital Paule de Viguier - CHU de Toulouse", "Toulouse"),

            "iuct oncopole": ("Institut Universitaire du Cancer de Toulouse - Oncopole", "Toulouse"),
            "iuct-oncopole": ("Institut Universitaire du Cancer de Toulouse - Oncopole", "Toulouse"),
            "claudius regaud": ("Institut Universitaire du Cancer de Toulouse - Oncopole", "Toulouse"),
            "institut universitaire du cancer de toulouse": ("Institut Universitaire du Cancer de Toulouse - Oncopole",
                                                             "Toulouse"),
            "institut universitaire du cancer toulouse": ("Institut Universitaire du Cancer de Toulouse - Oncopole",
                                                          "Toulouse"),
            "institut universitaire du cancer-toulouse": ("Institut Universitaire du Cancer de Toulouse - Oncopole",
                                                          "Toulouse"),
            "iuct toulouse": ("Institut Universitaire du Cancer de Toulouse - Oncopole", "Toulouse"),

            # CHU Lille - site level
            "claude huriez": ("Hôpital Claude-Huriez - CHU de Lille", "Lille"),
            "hopital claude huriez": ("Hôpital Claude-Huriez - CHU de Lille", "Lille"),
            "hôpital claude huriez": ("Hôpital Claude-Huriez - CHU de Lille", "Lille"),

            "roger salengro": ("Hôpital Roger-Salengro - CHU de Lille", "Lille"),
            "salengro": ("Hôpital Roger-Salengro - CHU de Lille", "Lille"),

            "hopital calmette lille": ("Hôpital Calmette - CHU de Lille", "Lille"),
            "hôpital calmette lille": ("Hôpital Calmette - CHU de Lille", "Lille"),
            "calmette lille": ("Hôpital Calmette - CHU de Lille", "Lille"),

            "jeanne de flandre": ("Hôpital Jeanne-de-Flandre - CHU de Lille", "Lille"),

            # CHU Nantes - site level
            "hotel dieu nantes": ("Hôtel-Dieu - CHU de Nantes", "Nantes"),
            "hôtel dieu nantes": ("Hôtel-Dieu - CHU de Nantes", "Nantes"),

            "nord laennec": ("Hôpital Nord-Laennec - CHU de Nantes", "Saint-Herblain"),
            "nord laënnec": ("Hôpital Nord-Laennec - CHU de Nantes", "Saint-Herblain"),
            "hopital nord laennec": ("Hôpital Nord-Laennec - CHU de Nantes", "Saint-Herblain"),
            "hôpital nord laennec": ("Hôpital Nord-Laennec - CHU de Nantes", "Saint-Herblain"),
            "guillaume rene laennec": ("Hôpital Nord-Laennec - CHU de Nantes", "Saint-Herblain"),
            "guillaume rené laennec": ("Hôpital Nord-Laennec - CHU de Nantes", "Saint-Herblain"),

            # CHU Grenoble - site level
            "hopital michallon": ("Hôpital Michallon - CHU Grenoble Alpes", "La Tronche"),
            "hôpital michallon": ("Hôpital Michallon - CHU Grenoble Alpes", "La Tronche"),
            "michallon": ("Hôpital Michallon - CHU Grenoble Alpes", "La Tronche"),

            "hopital couple enfant": ("Hôpital Couple-Enfant - CHU Grenoble Alpes", "La Tronche"),
            "hôpital couple enfant": ("Hôpital Couple-Enfant - CHU Grenoble Alpes", "La Tronche"),

            # CHU Nice - site level
            "pasteur nice": ("Hôpital Pasteur - CHU de Nice", "Nice"),
            "hopital pasteur nice": ("Hôpital Pasteur - CHU de Nice", "Nice"),
            "hôpital pasteur nice": ("Hôpital Pasteur - CHU de Nice", "Nice"),

            "archet": ("Hôpital l'Archet - CHU de Nice", "Nice"),
            "hopital archet": ("Hôpital l'Archet - CHU de Nice", "Nice"),
            "hôpital archet": ("Hôpital l'Archet - CHU de Nice", "Nice"),

            # CHU Strasbourg - site level
            "hautepierre": ("Hôpital de Hautepierre - Hôpitaux Universitaires de Strasbourg", "Strasbourg"),
            "hopital hautepierre": ("Hôpital de Hautepierre - Hôpitaux Universitaires de Strasbourg", "Strasbourg"),
            "hôpital hautepierre": ("Hôpital de Hautepierre - Hôpitaux Universitaires de Strasbourg", "Strasbourg"),
            "hautepierre strasbourg": ("Hôpital de Hautepierre - Hôpitaux Universitaires de Strasbourg", "Strasbourg"),
            "hopital de hautepierre": ("Hôpital de Hautepierre - Hôpitaux Universitaires de Strasbourg", "Strasbourg"),
            "hôpital de hautepierre": ("Hôpital de Hautepierre - Hôpitaux Universitaires de Strasbourg", "Strasbourg"),

            "nouvel hopital civil": ("Nouvel Hôpital Civil - Hôpitaux Universitaires de Strasbourg", "Strasbourg"),
            "nouvel hôpital civil": ("Nouvel Hôpital Civil - Hôpitaux Universitaires de Strasbourg", "Strasbourg"),
            "nouvel hopital civil strasbourg": ("Nouvel Hôpital Civil - Hôpitaux Universitaires de Strasbourg",
                                                "Strasbourg"),
            "nouvel hôpital civil strasbourg": ("Nouvel Hôpital Civil - Hôpitaux Universitaires de Strasbourg",
                                                "Strasbourg"),

            # CHU Montpellier - site level
            "saint eloi montpellier": ("Hôpital Saint-Éloi - CHU de Montpellier", "Montpellier"),
            "saint-éloi montpellier": ("Hôpital Saint-Éloi - CHU de Montpellier", "Montpellier"),
            "hopital saint eloi": ("Hôpital Saint-Éloi - CHU de Montpellier", "Montpellier"),

            "lapeyronie": ("Hôpital Lapeyronie - CHU de Montpellier", "Montpellier"),
            "hopital lapeyronie": ("Hôpital Lapeyronie - CHU de Montpellier", "Montpellier"),
            "hôpital lapeyronie": ("Hôpital Lapeyronie - CHU de Montpellier", "Montpellier"),

            "gui de chauliac": ("Hôpital Gui-de-Chauliac - CHU de Montpellier", "Montpellier"),

            # CHU Rennes - site level
            "pontchaillou": ("Hôpital Pontchaillou - CHU de Rennes", "Rennes"),
            "hopital pontchaillou": ("Hôpital Pontchaillou - CHU de Rennes", "Rennes"),
            "hôpital pontchaillou": ("Hôpital Pontchaillou - CHU de Rennes", "Rennes"),

            # CHU Rouen - site level
            "charles nicolle rouen": ("Hôpital Charles-Nicolle - CHU de Rouen", "Rouen"),
            "hopital charles nicolle": ("Hôpital Charles-Nicolle - CHU de Rouen", "Rouen"),
            "hôpital charles nicolle": ("Hôpital Charles-Nicolle - CHU de Rouen", "Rouen"),

            # CHU Dijon - site level
            "francois mitterrand dijon": ("Hôpital François-Mitterrand - CHU Dijon Bourgogne", "Dijon"),
            "françois mitterrand dijon": ("Hôpital François-Mitterrand - CHU Dijon Bourgogne", "Dijon"),
            "hopital francois mitterrand": ("Hôpital François-Mitterrand - CHU Dijon Bourgogne", "Dijon"),

            "hopital universitaire le bocage": ("Hôpital Le Bocage - CHU Dijon Bourgogne", "Dijon"),
            "hôpital universitaire le bocage": ("Hôpital Le Bocage - CHU Dijon Bourgogne", "Dijon"),
            "le bocage hospital": ("Hôpital Le Bocage - CHU Dijon Bourgogne", "Dijon"),

            # CHU Angers - site level
            "larrey angers": ("Hôpital Larrey - CHU d'Angers", "Angers"),

            # CHU Brest - site level
            "cavale blanche": ("Hôpital de la Cavale Blanche - CHU de Brest", "Brest"),
            "hopital cavale blanche": ("Hôpital de la Cavale Blanche - CHU de Brest", "Brest"),
            "hôpital cavale blanche": ("Hôpital de la Cavale Blanche - CHU de Brest", "Brest"),

            "morvan": ("Hôpital Morvan - CHU de Brest", "Brest"),
            "hopital morvan": ("Hôpital Morvan - CHU de Brest", "Brest"),

            # CHU Caen - site level
            "cote de nacre": ("Hôpital Côte de Nacre - CHU de Caen Normandie", "Caen"),
            "côte de nacre": ("Hôpital Côte de Nacre - CHU de Caen Normandie", "Caen"),

            # CHU Clermont-Ferrand - site level
            "gabriel montpied": ("Hôpital Gabriel-Montpied - CHU de Clermont-Ferrand", "Clermont-Ferrand"),
            "estaing": ("Hôpital Estaing - CHU de Clermont-Ferrand", "Clermont-Ferrand"),

            # CHU Limoges - site level
            "dupuytren limoges": ("Hôpital Dupuytren - CHU de Limoges", "Limoges"),
            "hopital dupuytren limoges": ("Hôpital Dupuytren - CHU de Limoges", "Limoges"),

            # CHU Nancy - site level
            "brabois": ("Hôpitaux de Brabois - CHRU de Nancy", "Vandœuvre-lès-Nancy"),
            "hopitaux de brabois": ("Hôpitaux de Brabois - CHRU de Nancy", "Vandœuvre-lès-Nancy"),
            "hôpitaux de brabois": ("Hôpitaux de Brabois - CHRU de Nancy", "Vandœuvre-lès-Nancy"),

            # CHU Nîmes - site level
            "caremeau": ("Hôpital Carémeau - CHU de Nîmes", "Nîmes"),
            "carémeau": ("Hôpital Carémeau - CHU de Nîmes", "Nîmes"),

            # CHU Poitiers - site level
            "la miletrie": ("Hôpital de la Milétrie - CHU de Poitiers", "Poitiers"),
            "milétrie": ("Hôpital de la Milétrie - CHU de Poitiers", "Poitiers"),
            "miletrie": ("Hôpital de la Milétrie - CHU de Poitiers", "Poitiers"),

            # CHU Reims - site level
            "robert debre reims": ("Hôpital Robert-Debré - CHU de Reims", "Reims"),
            "robert debré reims": ("Hôpital Robert-Debré - CHU de Reims", "Reims"),

            # CHU Saint-Étienne - site level
            "hopital nord saint etienne": ("Hôpital Nord - CHU de Saint-Étienne", "Saint-Étienne"),
            "hôpital nord saint etienne": ("Hôpital Nord - CHU de Saint-Étienne", "Saint-Étienne"),

            # CHRU Tours - site level
            "bretonneau tours": ("Hôpital Bretonneau - CHRU de Tours", "Tours"),
            "trousseau tours": ("Hôpital Trousseau - CHRU de Tours", "Chambray-lès-Tours"),

            "hopital nord": ("Hôpital Nord", "Marseille"),
            "hôpital nord": ("Hôpital Nord", "Marseille"),

            "sainte marguerite": ("Hôpital Sainte-Marguerite", "Marseille"),
            "ste marguerite": ("Hôpital Sainte-Marguerite", "Marseille"),

            "salvator": ("Hôpital Salvator", "Marseille"),

            "gustave roussy": ("Institut Gustave Roussy", "Villejuif"),

            "institut curie": ("Institut Curie", "Paris"),
            "curie institute": ("Institut Curie", "Paris"),

            # Lyon
            "hospices civils de lyon": ("Hospices Civils de Lyon", "Lyon"),
            "chu lyon": ("Hospices Civils de Lyon", "Lyon"),

            "centre leon berard": ("Centre Léon Bérard", "Lyon"),
            "centre léon bérard": ("Centre Léon Bérard", "Lyon"),
            "leon berard cancer center": ("Centre Léon Bérard", "Lyon"),
            "leon berard center": ("Centre Léon Bérard", "Lyon"),
            "léon bérard centre": ("Centre Léon Bérard", "Lyon"),

            # Marseille
            "ap hm": ("Assistance Publique - Hôpitaux de Marseille", "Marseille"),
            "aphm": ("Assistance Publique - Hôpitaux de Marseille", "Marseille"),
            "assistance publique hopitaux de marseille": ("Assistance Publique - Hôpitaux de Marseille", "Marseille"),
            "assistance publique hôpitaux de marseille": ("Assistance Publique - Hôpitaux de Marseille", "Marseille"),

            "institut paoli calmettes": ("Institut Paoli-Calmettes", "Marseille"),
            "institut paolicalmettes": ("Institut Paoli-Calmettes", "Marseille"),
            "paoli calmettes": ("Institut Paoli-Calmettes", "Marseille"),

            # Regional CHUs
            "chu de bordeaux": ("CHU de Bordeaux", "Bordeaux"),
            "chu bordeaux": ("CHU de Bordeaux", "Bordeaux"),
            "bordeaux university hospital": ("CHU de Bordeaux", "Bordeaux"),
            "hopital universitaire de bordeaux": ("CHU de Bordeaux", "Bordeaux"),
            "university hospital of bordeaux": ("CHU de Bordeaux", "Bordeaux"),

            "chu de lille": ("CHU de Lille", "Lille"),
            "chu lille": ("CHU de Lille", "Lille"),
            "lille university hospital": ("CHU de Lille", "Lille"),
            "centre hospitalo universitaire de lille": ("CHU de Lille", "Lille"),
            "centre hospitalo-universitaire de lille": ("CHU de Lille", "Lille"),
            "university lille hospital": ("CHU de Lille", "Lille"),

            "chu de nantes": ("CHU de Nantes", "Nantes"),
            "chu nantes": ("CHU de Nantes", "Nantes"),
            "nantes university hospital": ("CHU de Nantes", "Nantes"),
            "centre hospitalier universitaire de nantes": ("CHU de Nantes", "Nantes"),
            "university hospital nantes": ("CHU de Nantes", "Nantes"),

            "centre hospitalo universitaire de nancy": ("CHRU de Nancy", "Nancy"),

            "chu de rennes": ("CHU de Rennes", "Rennes"),
            "chu rennes": ("CHU de Rennes", "Rennes"),
            "rennes university hospital": ("CHU de Rennes", "Rennes"),

            "chu de rouen": ("CHU de Rouen", "Rouen"),
            "chu rouen": ("CHU de Rouen", "Rouen"),
            "rouen university hospital": ("CHU de Rouen", "Rouen"),
            "hopital universitaire de rouen": ("CHU de Rouen", "Rouen"),

            "university of rouen normandy": ("Université de Rouen Normandie", "Rouen"),
            "rouen university": ("Université de Rouen Normandie", "Rouen"),
            "universite de rouen normandie": ("Université de Rouen Normandie", "Rouen"),
            "université de rouen normandie": ("Université de Rouen Normandie", "Rouen"),

            "chu de toulouse": ("CHU de Toulouse", "Toulouse"),
            "chu toulouse": ("CHU de Toulouse", "Toulouse"),
            "toulouse university hospital": ("CHU de Toulouse", "Toulouse"),

            "chu de montpellier": ("CHU de Montpellier", "Montpellier"),
            "chu montpellier": ("CHU de Montpellier", "Montpellier"),
            "montpellier university hospital": ("CHU de Montpellier", "Montpellier"),
            "centre hospitalier universitaire de montpellier": ("CHU de Montpellier", "Montpellier"),

            "institut universitaire de recherche clinique": ("Institut Universitaire de Recherche Clinique (IURC)",
                                                             "Montpellier"),
            "institut universitaire de recherche clinique iurc": ("Institut Universitaire de Recherche Clinique (IURC)",
                                                                  "Montpellier"),
            "iurc montpellier": ("Institut Universitaire de Recherche Clinique (IURC)", "Montpellier"),

            "university federation of radiation oncology of mediterranean occitanie": (
                "University Federation of Radiation Oncology of Mediterranean Occitanie",
                "Montpellier"
            ),
            "federation of radiation oncology occitanie": (
                "University Federation of Radiation Oncology of Mediterranean Occitanie",
                "Montpellier"
            ),
            "radiation oncology occitanie": (
                "University Federation of Radiation Oncology of Mediterranean Occitanie",
                "Montpellier"
            ),

            "chu de grenoble": ("CHU Grenoble Alpes", "Grenoble"),
            "chu grenoble": ("CHU Grenoble Alpes", "Grenoble"),
            "grenoble university hospital": ("CHU Grenoble Alpes", "Grenoble"),
            "centre hospitalier universitaire grenoble alpes": ("CHU Grenoble Alpes", "Grenoble"),
            "university hospital of grenoble alpes": ("CHU Grenoble Alpes", "Grenoble"),

            "chu de nice": ("CHU de Nice", "Nice"),
            "chu nice": ("CHU de Nice", "Nice"),
            "nice university hospital": ("CHU de Nice", "Nice"),

            "chu de strasbourg": ("Hôpitaux Universitaires de Strasbourg", "Strasbourg"),
            "chu strasbourg": ("Hôpitaux Universitaires de Strasbourg", "Strasbourg"),
            "hopitaux universitaires de strasbourg": ("Hôpitaux Universitaires de Strasbourg", "Strasbourg"),
            "hôpitaux universitaires de strasbourg": ("Hôpitaux Universitaires de Strasbourg", "Strasbourg"),
            "strasbourg university hospital": ("Hôpitaux Universitaires de Strasbourg", "Strasbourg"),
            "hus strasbourg": ("Hôpitaux Universitaires de Strasbourg", "Strasbourg"),
            "university hospital of strasbourg": ("Hôpitaux Universitaires de Strasbourg", "Strasbourg"),

            "institut hospitalo universitaire": ("Institut Hospitalo-Universitaire (IHU) Strasbourg", "Strasbourg"),
            "institut hospitalo-universitaire": ("Institut Hospitalo-Universitaire (IHU) Strasbourg", "Strasbourg"),
            "ihu strasbourg": ("Institut Hospitalo-Universitaire (IHU) Strasbourg", "Strasbourg"),
            "institut hospitalo universitaire strasbourg": ("Institut Hospitalo-Universitaire (IHU) Strasbourg",
                                                            "Strasbourg"),
            "institut hospitalo-universitaire strasbourg": ("Institut Hospitalo-Universitaire (IHU) Strasbourg",
                                                            "Strasbourg"),

            # Cancer / research centers
            "institut bergonie": ("Institut Bergonié", "Bordeaux"),
            "institut bergonié": ("Institut Bergonié", "Bordeaux"),

            "institut claudius regaud": ("Institut Universitaire du Cancer de Toulouse - Oncopole", "Toulouse"),
            "oncopole toulouse": ("Institut Universitaire du Cancer de Toulouse - Oncopole", "Toulouse"),

            "centre eugene marquis": ("Centre Eugène Marquis", "Rennes"),
            "centre eugène marquis": ("Centre Eugène Marquis", "Rennes"),

            "centre henri becquerel": ("Centre Henri-Becquerel", "Rouen"),
            "centre antoine lacassagne": ("Centre Antoine Lacassagne", "Nice"),
            "antoine lacassagne centre": ("Centre Antoine Lacassagne", "Nice"),

            "institut de cancerologie de l'ouest": ("Institut de Cancérologie de l'Ouest", "Angers"),
            "institut de cancérologie de l'ouest": ("Institut de Cancérologie de l'Ouest", "Angers"),
            "ico": ("Institut de Cancérologie de l'Ouest", city_value.title() if city_value else ""),

            "centre oscar lambret": ("Centre Oscar Lambret", "Lille"),

            "institut regional du cancer de montpellier": ("Institut Régional du Cancer de Montpellier", "Montpellier"),
            "icm montpellier": ("Institut Régional du Cancer de Montpellier", "Montpellier"),

            "quai jules guesde": ("Sanofi", "Vitry-sur-Seine"),
            "sanofi oncology": ("Sanofi", "Vitry-sur-Seine"),
            "sanofi r&d": ("Sanofi", "Vitry-sur-Seine"),
            "sanofi aventis": ("Sanofi", "Vitry-sur-Seine"),

            "erytech pharma": ("Erytech Pharma", "Lyon"),

            "chu amiens": ("CHU Amiens-Picardie", "Amiens"),
            "chu de amiens": ("CHU Amiens-Picardie", "Amiens"),
            "amiens university hospital": ("CHU Amiens-Picardie", "Amiens"),
            "centre hospitalo universitaire amiens picardie": ("CHU Amiens-Picardie", "Amiens"),
            "centre hospitalo-universitaire amiens picardie": ("CHU Amiens-Picardie", "Amiens"),
            "center hospitalo universitaire amiens picardie": ("CHU Amiens-Picardie", "Amiens"),
            "center hospitalo-universitaire amiens picardie": ("CHU Amiens-Picardie", "Amiens"),
            "hopital universitaire d amiens": ("CHU Amiens-Picardie", "Amiens"),
            "hôpital universitaire d amiens": ("CHU Amiens-Picardie", "Amiens"),

            "chu angers": ("CHU d'Angers", "Angers"),
            "chu de angers": ("CHU d'Angers", "Angers"),
            "angers university hospital": ("CHU d'Angers", "Angers"),

            "chu besancon": ("CHU de Besançon", "Besançon"),
            "chu de besancon": ("CHU de Besançon", "Besançon"),
            "chu besançon": ("CHU de Besançon", "Besançon"),
            "chu de besançon": ("CHU de Besançon", "Besançon"),
            "besancon university hospital": ("CHU de Besançon", "Besançon"),

            "chu brest": ("CHU de Brest", "Brest"),
            "chu de brest": ("CHU de Brest", "Brest"),
            "brest university hospital": ("CHU de Brest", "Brest"),
            "university hospital of brest": ("CHU de Brest", "Brest"),

            "centre hospitalo universitaire de la reunion": ("CHU de La Réunion", "Saint-Denis"),
            "felix guyon university hospital": ("CHU de La Réunion", "Saint-Denis"),

            "centre hospitalier universitaire de la guadeloupe": ("CHU de la Guadeloupe", "Pointe-à-Pitre"),

            "chu caen": ("CHU de Caen Normandie", "Caen"),
            "chu de caen": ("CHU de Caen Normandie", "Caen"),
            "caen university hospital": ("CHU de Caen Normandie", "Caen"),
            "centre hospitalo universitaire de caen": ("CHU de Caen Normandie", "Caen"),
            "centre hospitalo-universitaire de caen": ("CHU de Caen Normandie", "Caen"),

            "chu clermont ferrand": ("CHU de Clermont-Ferrand", "Clermont-Ferrand"),
            "chu de clermont ferrand": ("CHU de Clermont-Ferrand", "Clermont-Ferrand"),
            "clermont ferrand university hospital": ("CHU de Clermont-Ferrand", "Clermont-Ferrand"),

            "chu dijon": ("CHU Dijon Bourgogne", "Dijon"),
            "chu de dijon": ("CHU Dijon Bourgogne", "Dijon"),
            "dijon university hospital": ("CHU Dijon Bourgogne", "Dijon"),

            "chu limoges": ("CHU de Limoges", "Limoges"),
            "chu de limoges": ("CHU de Limoges", "Limoges"),
            "limoges university hospital": ("CHU de Limoges", "Limoges"),

            "chu nimes": ("CHU de Nîmes", "Nîmes"),
            "chu de nimes": ("CHU de Nîmes", "Nîmes"),
            "chu nîmes": ("CHU de Nîmes", "Nîmes"),
            "chu de nîmes": ("CHU de Nîmes", "Nîmes"),
            "nimes university hospital": ("CHU de Nîmes", "Nîmes"),

            "chu poitiers": ("CHU de Poitiers", "Poitiers"),
            "chu de poitiers": ("CHU de Poitiers", "Poitiers"),
            "poitiers university hospital": ("CHU de Poitiers", "Poitiers"),

            "chu reims": ("CHU de Reims", "Reims"),
            "chu de reims": ("CHU de Reims", "Reims"),
            "reims university hospital": ("CHU de Reims", "Reims"),

            "chu saint etienne": ("CHU de Saint-Étienne", "Saint-Étienne"),
            "chu de saint etienne": ("CHU de Saint-Étienne", "Saint-Étienne"),
            "chu saint-etienne": ("CHU de Saint-Étienne", "Saint-Étienne"),
            "chu de saint-etienne": ("CHU de Saint-Étienne", "Saint-Étienne"),
            "saint etienne university hospital": ("CHU de Saint-Étienne", "Saint-Étienne"),
            "university hospital of saint etienne": ("CHU de Saint-Étienne", "Saint-Étienne"),
            "university hospital st etienne": ("CHU de Saint-Étienne", "Saint-Étienne"),
            "centre hospitalier universitaire st etienne": ("CHU de Saint-Étienne", "Saint-Étienne"),

            "chu tours": ("CHRU de Tours", "Tours"),
            "chu de tours": ("CHRU de Tours", "Tours"),
            "chru tours": ("CHRU de Tours", "Tours"),
            "tours university hospital": ("CHRU de Tours", "Tours"),
            "centre hospitalo universitaire de tours": ("CHRU de Tours", "Tours"),
            "university hospital of tours": ("CHRU de Tours", "Tours"),

            # More cancer centers
            "bergonie institute": ("Institut Bergonié", "Bordeaux"),
            "bergonié institute": ("Institut Bergonié", "Bordeaux"),

            "antoine lacassagne cancer center": ("Centre Antoine Lacassagne", "Nice"),
            "lacassagne center": ("Centre Antoine Lacassagne", "Nice"),

            "eugene marquis": ("Centre Eugène Marquis", "Rennes"),
            "eugène marquis": ("Centre Eugène Marquis", "Rennes"),

            "henri becquerel": ("Centre Henri-Becquerel", "Rouen"),

            "institut de cancerologie de louest": ("Institut de Cancérologie de l'Ouest", "Angers"),
            "cancerology institute of western france": ("Institut de Cancérologie de l'Ouest", "Angers"),
            "institut de cancerologie de l ouest": ("Institut de Cancérologie de l'Ouest", "Angers"),
            "cancer institute of west": ("Institut de Cancérologie de l'Ouest", "Angers"),

            "oscar lambret": ("Centre Oscar Lambret", "Lille"),

            "institut regional du cancer": ("Institut Régional du Cancer de Montpellier", "Montpellier"),
            "montpellier cancer institute": ("Institut Régional du Cancer de Montpellier", "Montpellier"),

            # Other common French hospitals / institutes
            "foch hospital": ("Hôpital Foch", "Suresnes"),
            "hopital foch": ("Hôpital Foch", "Suresnes"),
            "hôpital foch": ("Hôpital Foch", "Suresnes"),

            "hopital saint joseph paris": ("Hôpital Paris Saint-Joseph", "Paris"),
            "hôpital saint joseph paris": ("Hôpital Paris Saint-Joseph", "Paris"),
            "paris saint joseph hospital": ("Hôpital Paris Saint-Joseph", "Paris"),
            "hopital paris saint joseph": ("Hôpital Paris Saint-Joseph", "Paris"),
            "hôpital paris saint joseph": ("Hôpital Paris Saint-Joseph", "Paris"),
            "groupe hospitalier paris saint joseph": ("Groupe Hospitalier Paris Saint-Joseph", "Paris"),

            "hopital marie lannelongue": ("Hôpital Marie-Lannelongue", "Le Plessis-Robinson"),
            "hôpital marie lannelongue": ("Hôpital Marie-Lannelongue", "Le Plessis-Robinson"),

            "hopital saint camille": ("Hôpital Saint-Camille", "Bry-sur-Marne"),
            "hôpital saint camille": ("Hôpital Saint-Camille", "Bry-sur-Marne"),

            "institut mutualiste montsouris": ("Institut Mutualiste Montsouris", "Paris"),
            "montsouris institute": ("Institut Mutualiste Montsouris", "Paris"),
            "institut montsouris": ("Institut Mutualiste Montsouris", "Paris"),
            "montsouris institut": ("Institut Mutualiste Montsouris", "Paris"),

            "american hospital of paris": ("American Hospital of Paris", "Neuilly-sur-Seine"),
            "hopital americain de paris": ("American Hospital of Paris", "Neuilly-sur-Seine"),
            "hôpital américain de paris": ("American Hospital of Paris", "Neuilly-sur-Seine"),
            "american hospital in paris": ("American Hospital of Paris", "Neuilly-sur-Seine"),

            #####################################################3
            # AP-HP / Paris hospitals - extra variants
            "pitié salpêtrière hospital": ("Hôpital Pitié-Salpêtrière", "Paris"),
            "pitie salpetriere hospital": ("Hôpital Pitié-Salpêtrière", "Paris"),
            "hopital pitie salpetriere": ("Hôpital Pitié-Salpêtrière", "Paris"),
            "hopital pitie-salpetriere": ("Hôpital Pitié-Salpêtrière", "Paris"),
            "la pitie salpetriere": ("Hôpital Pitié-Salpêtrière", "Paris"),

            "georges pompidou european hospital": ("Hôpital européen Georges-Pompidou", "Paris"),
            "european georges pompidou hospital": ("Hôpital européen Georges-Pompidou", "Paris"),
            "hopital europeen georges pompidou": ("Hôpital européen Georges-Pompidou", "Paris"),

            "saint antoine hospital": ("Hôpital Saint-Antoine", "Paris"),
            "hospital saint antoine": ("Hôpital Saint-Antoine", "Paris"),
            "hopital saint antoine": ("Hôpital Saint-Antoine", "Paris"),

            "saint louis hospital": ("Hôpital Saint-Louis", "Paris"),
            "saint-louis hospital": ("Hôpital Saint-Louis", "Paris"),
            "hopital saint louis": ("Hôpital Saint-Louis", "Paris"),

            "necker enfants malades hospital": ("Hôpital Necker-Enfants malades", "Paris"),
            "necker-enfants malades hospital": ("Hôpital Necker-Enfants malades", "Paris"),
            "hopital necker enfants malades": ("Hôpital Necker-Enfants malades", "Paris"),

            "robert debre hospital": ("Hôpital Robert-Debré", "Paris"),
            "robert-debre hospital": ("Hôpital Robert-Debré", "Paris"),

            "armand trousseau hospital": ("Hôpital Armand-Trousseau", "Paris"),
            "armand-trousseau hospital": ("Hôpital Armand-Trousseau", "Paris"),

            "henry mondor": ("Hôpital Henri-Mondor", "Créteil"),
            "henry mondor university hospital": ("Hôpital Henri-Mondor", "Créteil"),
            "henri mondor university hospital": ("Hôpital Henri-Mondor", "Créteil"),
            "henri mondor hospital": ("Hôpital Henri-Mondor", "Créteil"),
            "hôpital henri mondor university hospital": ("Hôpital Henri-Mondor", "Créteil"),

            # AP-HM / Marseille
            "hopital de la timone": ("Hôpital de la Timone", "Marseille"),
            "hôpital de la timone": ("Hôpital de la Timone", "Marseille"),
            "timone hospital": ("Hôpital de la Timone", "Marseille"),

            "hopital de la conception": ("Hôpital de la Conception", "Marseille"),
            "hôpital de la conception": ("Hôpital de la Conception", "Marseille"),

            "hopital europeen marseille": ("Hôpital Européen Marseille", "Marseille"),
            "hôpital européen marseille": ("Hôpital Européen Marseille", "Marseille"),
            "european hospital of marseille": ("Hôpital Européen Marseille", "Marseille"),
            "european hospital marseille": ("Hôpital Européen Marseille", "Marseille"),

            # Lyon / HCL
            "edouard herriot hospital": ("Hôpital Édouard-Herriot - Hospices Civils de Lyon", "Lyon"),
            "hopital edouard herriot": ("Hôpital Édouard-Herriot - Hospices Civils de Lyon", "Lyon"),
            "hôpital edouard herriot": ("Hôpital Édouard-Herriot - Hospices Civils de Lyon", "Lyon"),
            "edouard-herriot hospital": ("Hôpital Édouard-Herriot - Hospices Civils de Lyon", "Lyon"),

            "hopital lyon sud": ("Hôpital Lyon Sud - Hospices Civils de Lyon", "Pierre-Bénite"),
            "hôpital lyon sud": ("Hôpital Lyon Sud - Hospices Civils de Lyon", "Pierre-Bénite"),
            "lyon sud hospital": ("Hôpital Lyon Sud - Hospices Civils de Lyon", "Pierre-Bénite"),
            "lyon sud university hospital": ("Hôpital Lyon Sud - Hospices Civils de Lyon", "Pierre-Bénite"),
            "centre hospitalier lyon sud": ("Hôpital Lyon Sud - Hospices Civils de Lyon", "Pierre-Bénite"),

            "hopital de la croix rousse": ("Hôpital de la Croix-Rousse - Hospices Civils de Lyon", "Lyon"),
            "hôpital de la croix rousse": ("Hôpital de la Croix-Rousse - Hospices Civils de Lyon", "Lyon"),
            "la croix rousse hospital": ("Hôpital de la Croix-Rousse - Hospices Civils de Lyon", "Lyon"),

            "hopital louis pradel": ("Hôpital Louis-Pradel - Hospices Civils de Lyon", "Bron"),
            "hôpital louis pradel": ("Hôpital Louis-Pradel - Hospices Civils de Lyon", "Bron"),

            # Cancer centers / Unicancer
            "paoli calmettes institute": ("Institut Paoli-Calmettes", "Marseille"),
            "paoli-calmettes institute": ("Institut Paoli-Calmettes", "Marseille"),
            "paoli calmette institute": ("Institut Paoli-Calmettes", "Marseille"),
            "paoli calmettes institut": ("Institut Paoli-Calmettes", "Marseille"),
            "centre paoli calmette": ("Institut Paoli-Calmettes", "Marseille"),

            "centre georges francois leclerc": ("Centre Georges-François Leclerc", "Dijon"),
            "centre georges-francois leclerc": ("Centre Georges-François Leclerc", "Dijon"),
            "georges francois leclerc cancer center": ("Centre Georges-François Leclerc", "Dijon"),
            "georges-francois leclerc cancer center": ("Centre Georges-François Leclerc", "Dijon"),

            "centre francois baclesse": ("Centre François-Baclesse", "Caen"),
            "centre françois baclesse": ("Centre François-Baclesse", "Caen"),
            "francois baclesse cancer center": ("Centre François-Baclesse", "Caen"),
            "cancer centre f baclesse": ("Centre François-Baclesse", "Caen"),

            "centre jean perrin": ("Centre Jean-Perrin", "Clermont-Ferrand"),
            "jean perrin cancer center": ("Centre Jean-Perrin", "Clermont-Ferrand"),

            "institut jean godinot": ("Institut Godinot", "Reims"),
            "jean godinot institut": ("Institut Godinot", "Reims"),
            "godinot cancer institute": ("Institut Godinot", "Reims"),

            "centre paul strauss": ("Centre Paul-Strauss", "Strasbourg"),

            "institut de cancerologie de lorraine": ("Institut de Cancérologie de Lorraine", "Vandœuvre-lès-Nancy"),
            "institut de cancérologie de lorraine": ("Institut de Cancérologie de Lorraine", "Vandœuvre-lès-Nancy"),
            "lorraine cancer institute": ("Institut de Cancérologie de Lorraine", "Vandœuvre-lès-Nancy"),
            "alexis vautrin": ("Institut de Cancérologie de Lorraine", "Vandœuvre-lès-Nancy"),

            "institut de cancerologie strasbourg europe": ("Institut de Cancérologie Strasbourg Europe", "Strasbourg"),
            "institut cancérologie strasbourg europe": ("Institut de Cancérologie Strasbourg Europe", "Strasbourg"),
            "icans": ("Institut de Cancérologie Strasbourg Europe", "Strasbourg"),

            # Private / non-CHU hospitals recurring enough
            "jean mermoz hospital": ("Hôpital Jean-Mermoz", "Lyon"),
            "hopital jean mermoz": ("Hôpital Jean-Mermoz", "Lyon"),
            "hôpital jean mermoz": ("Hôpital Jean-Mermoz", "Lyon"),
            "jean mermoz private hospital": ("Hôpital Jean-Mermoz", "Lyon"),
            "hopital prive jean mermoz": ("Hôpital Jean-Mermoz", "Lyon"),
            "hôpital privé jean mermoz": ("Hôpital Jean-Mermoz", "Lyon"),

            "groupe hospitalier diaconesses croix saint simon": ("Groupe Hospitalier Diaconesses Croix Saint-Simon",
                                                                 "Paris"),
            "diaconesses croix saint simon hospital": ("Groupe Hospitalier Diaconesses Croix Saint-Simon", "Paris"),
            "hopital diaconesses croix saint simon": ("Groupe Hospitalier Diaconesses Croix Saint-Simon", "Paris"),

            # Other CH / CHR hospitals that recur
            "centre hospitalier regional orleans": ("Centre Hospitalier Régional d'Orléans", "Orléans"),
            "centre hospitalier regional d orleans": ("Centre Hospitalier Régional d'Orléans", "Orléans"),
            "orleans regional hospital": ("Centre Hospitalier Régional d'Orléans", "Orléans"),
            "university hospital of orleans": ("Centre Hospitalier Régional d'Orléans", "Orléans"),
            "centre hospitalier universitaire orleans": ("Centre Hospitalier Régional d'Orléans", "Orléans"),
            "center hospitalier universitaire orleans": ("Centre Hospitalier Régional d'Orléans", "Orléans"),

            "la source hospital": ("Hôpital La Source - CHR d'Orléans", "Orléans"),

            "centre hospitalier intercommunal de poissy saint germain en laye": (
                "Centre Hospitalier Intercommunal de Poissy/Saint-Germain-en-Laye", "Poissy"),
            "poissy and saint germain hospital": ("Centre Hospitalier Intercommunal de Poissy/Saint-Germain-en-Laye",
                                                  "Poissy"),

            "centre hospitalier annecy genevois": ("Centre Hospitalier Annecy Genevois", "Annecy"),
            "annecy genevois hospital": ("Centre Hospitalier Annecy Genevois", "Annecy"),
            "hospital of annecy genevois": ("Centre Hospitalier Annecy Genevois", "Annecy"),

            "centre hospitalier cote basque": ("Centre Hospitalier de la Côte Basque", "Bayonne"),
            "centre hospitalier de la cote basque": ("Centre Hospitalier de la Côte Basque", "Bayonne"),

            "centre hospitalier de cayenne": ("Centre Hospitalier de Cayenne", "Cayenne"),
            "martinique hospital": ("Centre Hospitalier Universitaire de Martinique", "Fort-de-France"),
            "centre hospitalier universitaire de martinique": ("Centre Hospitalier Universitaire de Martinique",
                                                               "Fort-de-France"),

            "institut galien paris saclay": ("Institut Galien Paris-Saclay", "Paris-Saclay"),
            "institut des neurosciences paris saclay": ("Institut des Neurosciences Paris-Saclay", "Paris-Saclay"),
            "paris saclay cancer cluster": ("Paris Saclay Cancer Cluster", "Villejuif"),

            "versailles st quentin en yvelines paris saclay university": (
                "Université de Versailles Saint-Quentin-en-Yvelines",
                "Versailles"
            ),
            "universite versailles saint quentin en yvelines paris saclay": (
                "Université de Versailles Saint-Quentin-en-Yvelines",
                "Versailles"
            ),
            "versailles saint quentin en yvelines university": ("Université de Versailles Saint-Quentin-en-Yvelines",
                                                                "Versailles"),

            # Paris
            "universite paris cite": ("Université Paris Cité", "Paris"),
            "université paris cité": ("Université Paris Cité", "Paris"),
            "university paris cite": ("Université Paris Cité", "Paris"),

            "sorbonne universite": ("Sorbonne Université", "Paris"),
            "sorbonne université": ("Sorbonne Université", "Paris"),
            "sorbonne university": ("Sorbonne Université", "Paris"),

            "universite paris saclay": ("Université Paris-Saclay", "Paris-Saclay"),
            "université paris-saclay": ("Université Paris-Saclay", "Paris-Saclay"),
            "paris saclay university": ("Université Paris-Saclay", "Paris-Saclay"),
            "université paris saclay": ("Université Paris-Saclay", "Paris-Saclay"),
            "paris-saclay university": ("Université Paris-Saclay", "Paris-Saclay"),
            "paris saclay": ("Université Paris-Saclay", "Paris-Saclay"),
            "universite paris-saclay": ("Université Paris-Saclay", "Paris-Saclay"),
            "paris sud university": ("Université Paris-Saclay", "Paris-Saclay"),

            "universite paris est creteil": ("Université Paris-Est Créteil", "Créteil"),
            "université paris-est créteil": ("Université Paris-Est Créteil", "Créteil"),
            "paris est creteil university": ("Université Paris-Est Créteil", "Créteil"),
            "université paris est créteil": ("Université Paris-Est Créteil", "Créteil"),
            "universite paris-est creteil": ("Université Paris-Est Créteil", "Créteil"),
            "universite paris est-creteil": ("Université Paris-Est Créteil", "Créteil"),
            "université paris est-creteil": ("Université Paris-Est Créteil", "Créteil"),
            "university paris est creteil": ("Université Paris-Est Créteil", "Créteil"),
            "paris-est creteil university": ("Université Paris-Est Créteil", "Créteil"),
            "universite paris est": ("Université Paris-Est Créteil", "Créteil"),
            "université paris est": ("Université Paris-Est Créteil", "Créteil"),

            "universite paris sorbonne nord": ("Université Sorbonne Paris Nord", "Paris"),
            "université sorbonne paris nord": ("Université Sorbonne Paris Nord", "Paris"),

            "universite paris nanterre": ("Université Paris Nanterre", "Nanterre"),
            "université paris nanterre": ("Université Paris Nanterre", "Nanterre"),

            "universite paris dauphine": ("Université Paris Dauphine - PSL", "Paris"),
            "université paris dauphine": ("Université Paris Dauphine - PSL", "Paris"),

            "psl research university": ("Université PSL", "Paris"),
            "universite psl": ("Université PSL", "Paris"),

            "université paris-cité": ("Université Paris Cité", "Paris"),
            "universite paris-cite": ("Université Paris Cité", "Paris"),
            "université pariscité": ("Université Paris Cité", "Paris"),
            "universite pariscite": ("Université Paris Cité", "Paris"),
            "université pari cité": ("Université Paris Cité", "Paris"),
            "universite pari cite": ("Université Paris Cité", "Paris"),
            "université paris citè": ("Université Paris Cité", "Paris"),
            "university paris cité": ("Université Paris Cité", "Paris"),
            "university of paris cite": ("Université Paris Cité", "Paris"),
            "university of paris cité": ("Université Paris Cité", "Paris"),
            "paris cite university": ("Université Paris Cité", "Paris"),
            "paris cité university": ("Université Paris Cité", "Paris"),
            "universite de paris cite": ("Université Paris Cité", "Paris"),
            "université de paris cité": ("Université Paris Cité", "Paris"),
            "universite de paris-cite": ("Université Paris Cité", "Paris"),
            "université de paris-cité": ("Université Paris Cité", "Paris"),
            "universite de paris": ("Université Paris Cité", "Paris"),
            "université de paris": ("Université Paris Cité", "Paris"),
            "universite paris": ("Université Paris Cité", "Paris"),
            "université paris": ("Université Paris Cité", "Paris"),
            "university of paris": ("Université Paris Cité", "Paris"),
            "university of paris-centre": ("Université Paris Cité", "Paris"),
            "universite paris descartes": ("Université Paris Cité", "Paris"),
            "université paris descartes": ("Université Paris Cité", "Paris"),
            "universite paris descartes paris 5": ("Université Paris Cité", "Paris"),
            "paris descartes university": ("Université Paris Cité", "Paris"),
            "universite paris diderot": ("Université Paris Cité", "Paris"),
            "université paris diderot": ("Université Paris Cité", "Paris"),
            "universite paris diderot paris 7": ("Université Paris Cité", "Paris"),
            "université paris diderot paris 7": ("Université Paris Cité", "Paris"),
            "paris diderot university": ("Université Paris Cité", "Paris"),

            "sorbonne-universite": ("Sorbonne Université", "Paris"),
            "sorbonne-université": ("Sorbonne Université", "Paris"),

            "université psl": ("Université PSL", "Paris"),
            "paris sciences lettres research university": ("Université PSL", "Paris"),
            "paris sciences & lettres research university": ("Université PSL", "Paris"),

            "universite paris dauphine psl": ("Université Paris Dauphine - PSL", "Paris"),
            "université paris dauphine psl": ("Université Paris Dauphine - PSL", "Paris"),

            "universite sorbonne paris nord": ("Université Sorbonne Paris Nord", "Villetaneuse"),
            "sorbonne paris nord university": ("Université Sorbonne Paris Nord", "Villetaneuse"),
            "universite paris 13": ("Université Sorbonne Paris Nord", "Villetaneuse"),
            "université paris 13": ("Université Sorbonne Paris Nord", "Villetaneuse"),
            "university paris 13": ("Université Sorbonne Paris Nord", "Villetaneuse"),

            "institut universitaire de france": ("Institut Universitaire de France", "Paris"),
            "institut universitaire de france iuf": ("Institut Universitaire de France", "Paris"),
            "iuf": ("Institut Universitaire de France", "Paris"),

            # Lyon
            "universite de lyon": ("Université de Lyon", "Lyon"),
            "université de lyon": ("Université de Lyon", "Lyon"),
            "university of lyon": ("Université de Lyon", "Lyon"),
            "univ lyon": ("Université de Lyon", "Lyon"),

            "universite claude bernard": ("Université Claude Bernard Lyon 1", "Lyon"),
            "université claude bernard": ("Université Claude Bernard Lyon 1", "Lyon"),
            "lyon 1 university": ("Université Claude Bernard Lyon 1", "Lyon"),
            "lyon university 1": ("Université Claude Bernard Lyon 1", "Lyon"),
            "université lyon 1": ("Université Claude Bernard Lyon 1", "Lyon"),
            "university claudebernard": ("Université Claude Bernard Lyon 1", "Lyon"),
            "claude bernard university": ("Université Claude Bernard Lyon 1", "Lyon"),

            # Marseille
            "aix marseille univ": ("Aix-Marseille Université", "Marseille"),
            "aix-marseille university": ("Aix-Marseille Université", "Marseille"),
            "universite aix marseille": ("Aix-Marseille Université", "Marseille"),
            "université aix marseille": ("Aix-Marseille Université", "Marseille"),
            "universite d aix marseille": ("Aix-Marseille Université", "Marseille"),
            "université d aix marseille": ("Aix-Marseille Université", "Marseille"),
            "université d'aix marseille": ("Aix-Marseille Université", "Marseille"),

            # Bordeaux
            "universite de bordeaux": ("Université de Bordeaux", "Bordeaux"),
            "université de bordeaux": ("Université de Bordeaux", "Bordeaux"),
            "university of bordeaux": ("Université de Bordeaux", "Bordeaux"),
            "bordeaux medicine university": ("Université de Bordeaux", "Bordeaux"),

            # Toulouse
            "universite toulouse iii": ("Université Toulouse III - Paul Sabatier", "Toulouse"),
            "université toulouse iii": ("Université Toulouse III - Paul Sabatier", "Toulouse"),
            "paul sabatier university": ("Université Toulouse III - Paul Sabatier", "Toulouse"),
            "universite toulouse-iii paul sabatier": ("Université Toulouse III - Paul Sabatier", "Toulouse"),
            "université toulouse-iii paul-sabatier": ("Université Toulouse III - Paul Sabatier", "Toulouse"),
            "universite paul sabatier": ("Université Toulouse III - Paul Sabatier", "Toulouse"),
            "université paul sabatier": ("Université Toulouse III - Paul Sabatier", "Toulouse"),

            "universite de toulouse": ("Université de Toulouse", "Toulouse"),
            "université de toulouse": ("Université de Toulouse", "Toulouse"),
            "toulouse university": ("Université de Toulouse", "Toulouse"),
            "university of toulouse": ("Université de Toulouse", "Toulouse"),

            # Lille
            "universite de lille": ("Université de Lille", "Lille"),
            "université de lille": ("Université de Lille", "Lille"),
            "university of lille": ("Université de Lille", "Lille"),
            "lille university": ("Université de Lille", "Lille"),
            "university lille": ("Université de Lille", "Lille"),

            # Montpellier
            "universite de montpellier": ("Université de Montpellier", "Montpellier"),
            "université de montpellier": ("Université de Montpellier", "Montpellier"),
            "university of montpellier": ("Université de Montpellier", "Montpellier"),
            "montpellier university": ("Université de Montpellier", "Montpellier"),

            # Strasbourg
            "universite de strasbourg": ("Université de Strasbourg", "Strasbourg"),
            "université de strasbourg": ("Université de Strasbourg", "Strasbourg"),
            "university of strasbourg": ("Université de Strasbourg", "Strasbourg"),
            "strasbourg university": ("Université de Strasbourg", "Strasbourg"),

            # Grenoble
            "universite grenoble alpes": ("Université Grenoble Alpes", "Grenoble"),
            "université grenoble alpes": ("Université Grenoble Alpes", "Grenoble"),
            "grenoble alpes university": ("Université Grenoble Alpes", "Grenoble"),
            "universite grenoble-alpes": ("Université Grenoble Alpes", "Grenoble"),
            "université grenoble-alpes": ("Université Grenoble Alpes", "Grenoble"),
            "univ grenoble alpes": ("Université Grenoble Alpes", "Grenoble"),
            "univ. grenoble alpes": ("Université Grenoble Alpes", "Grenoble"),
            "university grenoble alpes": ("Université Grenoble Alpes", "Grenoble"),
            "universite de grenoble alpes": ("Université Grenoble Alpes", "Grenoble"),
            "université de grenoble alpes": ("Université Grenoble Alpes", "Grenoble"),
            "universite de grenoble-alpes": ("Université Grenoble Alpes", "Grenoble"),
            "université de grenoble-alpes": ("Université Grenoble Alpes", "Grenoble"),

            # Rennes
            "universite de rennes": ("Université de Rennes", "Rennes"),
            "université de rennes": ("Université de Rennes", "Rennes"),
            "rennes university": ("Université de Rennes", "Rennes"),

            # Nantes
            "universite de nantes": ("Nantes Université", "Nantes"),
            "université de nantes": ("Nantes Université", "Nantes"),
            "nantes universite": ("Nantes Université", "Nantes"),

            # Nice
            "universite cote d azur": ("Université Côte d'Azur", "Nice"),
            "université côte d azur": ("Université Côte d'Azur", "Nice"),
            "université côte d'azur": ("Université Côte d'Azur", "Nice"),
            "universite nice sophia antipolis": ("Université Côte d'Azur", "Nice"),

            # Reims
            "universite de reims champagne ardenne": ("Université de Reims Champagne-Ardenne", "Reims"),
            "université de reims champagne ardenne": ("Université de Reims Champagne-Ardenne", "Reims"),
            "universite de reims-champagne-ardenne": ("Université de Reims Champagne-Ardenne", "Reims"),
            "université de reims-champagne-ardenne": ("Université de Reims Champagne-Ardenne", "Reims"),
            "university of reims champagne ardenne": ("Université de Reims Champagne-Ardenne", "Reims"),
            "reims champagne ardenne university": ("Université de Reims Champagne-Ardenne", "Reims"),
            "university reims champagne ardenne": ("Université de Reims Champagne-Ardenne", "Reims"),
            "urca": ("Université de Reims Champagne-Ardenne", "Reims"),

            # Dijon
            "universite de bourgogne": ("Université de Bourgogne", "Dijon"),
            "université de bourgogne": ("Université de Bourgogne", "Dijon"),
            "universite bourgogne europe": ("Université de Bourgogne", "Dijon"),
            "université bourgogne europe": ("Université de Bourgogne", "Dijon"),
            "university of bourgogne": ("Université de Bourgogne", "Dijon"),
            "university of burgundy": ("Université de Bourgogne", "Dijon"),

            # Angers
            "universite d angers": ("Université d'Angers", "Angers"),
            "université d angers": ("Université d'Angers", "Angers"),

            # Poitiers
            "universite de poitiers": ("Université de Poitiers", "Poitiers"),
            "université de poitiers": ("Université de Poitiers", "Poitiers"),

            # Tours
            "universite de tours": ("Université de Tours", "Tours"),
            "université de tours": ("Université de Tours", "Tours"),

            # Clermont-Ferrand
            "universite clermont auvergne": ("Université Clermont Auvergne", "Clermont-Ferrand"),
            "université clermont auvergne": ("Université Clermont Auvergne", "Clermont-Ferrand"),
            "clermont auvergne university": ("Université Clermont Auvergne", "Clermont-Ferrand"),

            # Limoges
            "universite de limoges": ("Université de Limoges", "Limoges"),
            "université de limoges": ("Université de Limoges", "Limoges"),
            "univ limoges": ("Université de Limoges", "Limoges"),

            # Amiens
            "universite de picardie jules verne": ("Université de Picardie Jules Verne", "Amiens"),
            "université de picardie jules verne": ("Université de Picardie Jules Verne", "Amiens"),
            "universite de picardie-jules verne": ("Université de Picardie Jules Verne", "Amiens"),
            "université de picardie-jules verne": ("Université de Picardie Jules Verne", "Amiens"),
            "university of picardie jules verne": ("Université de Picardie Jules Verne", "Amiens"),
            "university of picardie jules vernes": ("Université de Picardie Jules Verne", "Amiens"),
            "picardie jules verne university": ("Université de Picardie Jules Verne", "Amiens"),

            # Caen
            "universite de caen normandie": ("Université de Caen Normandie", "Caen"),
            "université de caen normandie": ("Université de Caen Normandie", "Caen"),
            "normandie universite": ("Université de Caen Normandie", "Caen"),
            "normandie université": ("Université de Caen Normandie", "Caen"),
            "france normandie universite": ("Université de Caen Normandie", "Caen"),
            "france-normandie universite": ("Université de Caen Normandie", "Caen"),
            "caen normandie university": ("Université de Caen Normandie", "Caen"),

            # Nancy / Lorraine
            "universite de lorraine": ("Université de Lorraine", "Nancy"),
            "université de lorraine": ("Université de Lorraine", "Nancy"),
            "universite lorraine": ("Université de Lorraine", "Nancy"),

            # Besançon
            "universite de franche comte": ("Université de Franche-Comté", "Besançon"),
            "université de franche comté": ("Université de Franche-Comté", "Besançon"),

            #####
            # Rouen

            # Bretagne Occidentale
            "universite bretagne occidentale": ("Université de Bretagne Occidentale", "Brest"),
            "université bretagne occidentale": ("Université de Bretagne Occidentale", "Brest"),

            # Réunion
            "universite de reunion": ("Université de La Réunion", "Saint-Denis"),
            "université de réunion": ("Université de La Réunion", "Saint-Denis"),

            # Compiègne
            "universite de technologie de compiegne": ("Université de Technologie de Compiègne", "Compiègne"),

            # Littoral
            "universite du littoral cote d opale": ("Université du Littoral Côte d'Opale", "Dunkerque"),

            # Cergy
            "cy cergy paris universite": ("CY Cergy Paris Université", "Cergy"),

            # Limoges (variant)

            # Pau
            "universite de pau et des pays de ladour": ("Université de Pau et des Pays de l'Adour", "Pau"),

            # Antilles
            "univ antilles": ("Université des Antilles", "Pointe-à-Pitre"),

            # Gustave Eiffel
            "universite gustave eiffel": ("Université Gustave Eiffel", "Marne-la-Vallée"),

        }

        for alias, (fixed_hco, fixed_city) in alias_map.items():
            alias_norm = self.normalize_hco(alias)
            if alias_norm in hco_norm or alias_norm in aff_norm:
                ans = dept_value, fixed_hco, fixed_city
                break

        return ans

    def get_HCO_and_dept(self, df, first_cols, dedupe_level="hco"):
        self.df = df.copy()

        self.set_HCO_DEPT_SCORES()

        affs = self.df["Affiliations"]
        current_cities = self.df["City"].tolist()

        departments = []
        hcos = []
        cities = []



        for city_value,aff in zip(current_cities,affs):
            if not isinstance(aff, str) or aff.strip()=="":
                departments.append("")
                hcos.append("")
                cities.append(city_value)
                continue

            parts = [p.strip() for p in aff.split(",") if p.strip()]

            dept_value = self._best_scored_match(parts, self.DEPT_SCORES)
            hco_value = self._best_scored_match(parts, self.HCO_SCORES, ["department", "dept"])

            # fallback: if neither found and there are exactly 3 parts, use the first part as HCO
            if not hco_value:
                dept_value = ""
                hco_value = parts[0]

            if self.country.lower() == "germany":
                dept_value,hco_value, city_value = self.fix_Germany(dept_value,hco_value, city_value,aff)

            elif self.country.lower() == "italy":
                dept_value,hco_value, city_value = self.fix_Italy(dept_value,hco_value, city_value)

            if self.country.lower() == "france":
                dept_value,hco_value, city_value = self.fix_France(dept_value,hco_value, city_value,aff)

            departments.append(dept_value)
            hcos.append(hco_value)
            cities.append(city_value.title())

        for col in ["HCO", "Department"]:
            if col in self.df.columns:
                self.df.drop(columns=col, inplace=True)

        self.df["HCO"] = hcos
        self.df["Department"] = departments
        self.df["City"] = cities

        # ---------------------------------
        # DEDUPLICATION
        # ---------------------------------
        if dedupe_level == "hco":
            self.df["title_norm"] = self.df["Title"].fillna("").str.strip().str.lower()
            self.df["hco_norm"] = self.df["HCO"].fillna("").str.strip().str.lower()

            self.df = (
                self.df
                .drop_duplicates(subset=["title_norm", "hco_norm"], keep="first")
                .drop(columns=["title_norm", "hco_norm"])
            )

        elif dedupe_level == "author":
            dedupe_cols = [c for c in ["Author", "Author key", "URL"] if c in self.df.columns]
            if dedupe_cols:
                self.df = self.df.drop_duplicates(subset=dedupe_cols, keep="first").reset_index(drop=True)

        elif dedupe_level in [None, "none"]:
            pass

        cols = first_cols + [c for c in self.df.columns if c not in first_cols]
        self.df = self.df[cols].copy()

        return self.df