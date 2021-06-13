"""
    Fichier : gestion_droits_wtf_forms.py
    Auteur : OM 2021.03.22
    Gestion des formulaires avec WTF
"""
from flask_wtf import FlaskForm
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms.validators import Length, DataRequired
from wtforms.validators import Regexp


class FormWTFAjouterpersonnes(FlaskForm):
    """
        Dans le formulaire "contenus_ajouter_wtf.html" on impose que le champ soit rempli.
        Définition d'un "bouton" submit avec un libellé personnalisé.
    """
    nom_contenu_regexp = "^([A-Z]|[a-zÀ-ÖØ-öø-ÿ])[A-Za-zÀ-ÖØ-öø-ÿ]*['\- ]?[A-Za-zÀ-ÖØ-öø-ÿ]+$"
    nom_nompersonne_wtf = StringField("Clavioter le nom ", validators=[Length(min=2, max=20, message="min 2 max 20")])
    nom_prenompersonne_wtf = StringField("le nombre de prenom ", validators=[Length(min=2, max=20, message="min 2 max 20")])
    nom_datepersonne_wtf = StringField("la date de naissance ", validators=[Length(min=2, max=20, message="min 2 max 20")])
    adressemailpersonne_wtf = StringField("L'adresse Mail ", validators=[Length(min=2, max=50, message="min 2 max 20")])
    nom_mdppersonne_wtf = StringField("Mot de passe ", validators=[Length(min=2, max=20, message="min 2 max 20")])

    submit = SubmitField("Enregistrer contenu")
    submit_btn_ok_dplist_piece = SubmitField("Choix de la piece")

class FormWTFUpdatePersonne(FlaskForm):
    """
        Dans le formulaire "contenu_update_wtf.html" on impose que le champ soit rempli.
        Définition d'un "bouton" submit avec un libellé personnalisé.
    """
    nom_contenu_update_regexp = "^([A-Z]|[a-zÀ-ÖØ-öø-ÿ])[A-Za-zÀ-ÖØ-öø-ÿ]*['\- ]?[A-Za-zÀ-ÖØ-öø-ÿ]+$"
    nom_nompersonne_update_wtf = StringField("Clavioter le nom ", validators=[Length(min=2, max=20, message="min 2 max 20")])
    nom_prenompersonne_update_wtf = StringField("le nombre de prenom ", validators=[Length(min=2, max=20, message="min 2 max 20")])
    nom_datepersonne_update_wtf = StringField("L'endroit ou la date ", validators=[Length(min=2, max=20, message="min 2 max 20")])
    adressemailpersonne_update_wtf = StringField("L'endroit ou la date ", validators=[Length(min=2, max=50, message="min 2 max 50")])
    nom_mdppersonne_update_wtf = StringField("L'endroit ou la date ", validators=[Length(min=2, max=50, message="min 2 max 50")])

    submit = SubmitField("Update contenu")

    class DemoFormSelectWTF(FlaskForm):

        pieces_dropdown_wtf = SelectField('Pieces (liste déroulante)',
                                          validators=[DataRequired(message="Sélectionner un genre.")],
                                          validate_choice=False
                                          )
        # Alternative qui correspond aux lignes en commentaires lignes 88 et 89 du "gestion_wtf_forms_demo_select.py"
        # genres_dropdown_wtf = SelectField('Genres (liste déroulante)',
        #                                   validators=[DataRequired(message="Sélectionner un genre.")],
        #                                   validate_choice=False,
        #                                   coerce=int
        #                                   )
        submit_btn_ok_dplist_piece = SubmitField("Choix de la piece")

class FormWTFDeletepersonne(FlaskForm):
    """
        Dans le formulaire "contenu_delete_wtf.html"

        nom_contenu_delete_wtf : Champ qui reçoit la valeur du contenu, lecture seule. (readonly=true)
        submit_btn_del : Bouton d'effacement "DEFINITIF".
        submit_btn_conf_del : Bouton de confirmation pour effacer un "contenu".
        submit_btn_annuler : Bouton qui permet d'afficher la table "t_contenu".
    """


    nom_personne_delete_wtf = StringField("Effacer ce contenu")
    nb_personne_delete_wtf = StringField("")
    submit_btn_del = SubmitField("Effacer contenu")
    submit_btn_conf_del = SubmitField("Etes-vous sur d'effacer ?")
    submit_btn_annuler = SubmitField("Annuler")




class FormWTFAjouterDetails(FlaskForm):
    """
               Dans le formulaire "personnes_ajouter_wtf.html" on impose que le champ soit rempli.
               Définition d'un "bouton" submit avec un libellé personnalisé.
           """

    droit_wtf = StringField("Taper le prénom du collaborateur ",
                            validators=[Length(min=2, max=40, message="min 2 max 20")],
                            )

    submit = SubmitField("Enregistrer details")