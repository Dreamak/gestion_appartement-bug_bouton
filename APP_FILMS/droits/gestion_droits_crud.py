"""
    Fichier : gestion_droits_crud.py
    Auteur : OM 2021.05.01
    Gestions des "routes" FLASK et des données pour l'association entre les films et les genres.
"""
import sys

import pymysql
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for

from APP_FILMS import obj_mon_application
from APP_FILMS.database.connect_db_context_manager import MaBaseDeDonnee
from APP_FILMS.erreurs.exceptions import *
from APP_FILMS.erreurs.msg_erreurs import *
from APP_FILMS.contenus.gestion_contenus_wtf_forms import FormWTFAjouterDetails
from APP_FILMS.droits.gestion_droits_wtf_forms import FormWTFAjouterpersonnes
from APP_FILMS.droits.gestion_droits_wtf_forms import FormWTFUpdatePersonne
from APP_FILMS.droits.gestion_droits_wtf_forms import FormWTFDeletepersonne

"""
    Nom : personnes_droits_afficher
    Auteur : OM 2021.05.01
    Définition d'une "route" /personnes_droits_afficher
    
    But : Afficher les films avec les genres associés pour chaque film.
    
    Paramètres : id_genre_sel = 0 >> tous les films.
                 id_genre_sel = "n" affiche le film dont l'id est "n"
                 
"""


@obj_mon_application.route("/personnes_droits_afficher/<int:id_droit_sel>", methods=['GET', 'POST'])
def personnes_droits_afficher(id_droit_sel):
    if request.method == "GET":
        try:
            try:
                # Renvoie une erreur si la connexion est perdue.
                MaBaseDeDonnee().connexion_bd.ping(False)
            except Exception as Exception_init_droits_afficher:
                code, msg = Exception_init_droits_afficher.args
                flash(f"{error_codes.get(code, msg)} ", "danger")
                flash(f"Exception _init_personnes_droits_afficher problème de connexion BD : {sys.exc_info()[0]} "
                      f"{Exception_init_droits_afficher.args[0]} , "
                      f"{Exception_init_droits_afficher}", "danger")
                raise MaBdErreurConnexion(f"{msg_erreurs['ErreurConnexionBD']['message']} {erreur.args[0]}")

            with MaBaseDeDonnee().connexion_bd.cursor() as mc_afficher:
                strsql_droits_afficher_data = """SELECT t_personne.id_personne, t_personne.Nom_personne, t_personne.Prenom_personne, t_personne.Date_naissance_personne, t_personne.Adresse_mail_personne, t_personne.MDP_personne FROM t_personne ORDER BY id_personne ASC"""


                if id_droit_sel == 0:
                    # le paramètre 0 permet d'afficher tous les films
                    # Sinon le paramètre représente la valeur de l'id du film
                    mc_afficher.execute(strsql_droits_afficher_data)
                else:
                    # Constitution d'un dictionnaire pour associer l'id du film sélectionné avec un nom de variable
                    valeur_id_droit_selected_dictionnaire = {"value_id_droit_selected": id_droit_sel}
                    # En MySql l'instruction HAVING fonctionne comme un WHERE... mais doit être associée à un GROUP BY
                    # L'opérateur += permet de concaténer une nouvelle valeur à la valeur de gauche préalablement définie.
                    strsql_droits_afficher_data += """ HAVING id_droit= %(value_id_droit_selected)s"""

                    mc_afficher.execute(strsql_droits_afficher_data, valeur_id_droit_selected_dictionnaire)

                # Récupère les données de la requête.
                data_droits_afficher = mc_afficher.fetchall()
                print("data_droits ", data_droits_afficher, " Type : ", type(data_droits_afficher))

                # Différencier les messages.
                if not data_droits_afficher and id_droit_sel == 0:
                    flash("""La table "t_personne" est vide. !""", "warning")
                elif not data_droits_afficher and id_droit_sel > 0:
                    # Si l'utilisateur change l'id_film dans l'URL et qu'il ne correspond à aucun film
                    flash(f"Le droit {id_droit_sel} demandé n'existe pas !!", "warning")
                else:
                    flash(f"Données personnes et droits affichés !!", "success")

        except Exception as Exception_droits_afficher:
            code, msg = Exception_droits_afficher.args
            flash(f"{error_codes.get(code, msg)} ", "danger")
            flash(f"Exception personnes_droits_afficher : {sys.exc_info()[0]} "
                  f"{Exception_droits_afficher.args[0]} , "
                  f"{Exception_droits_afficher}", "danger")

    # Envoie la page "HTML" au serveur.
    return render_template("droits/personnes_droits_afficher.html", data=data_droits_afficher)

"""
    nom: edit_droit_selected
    On obtient un objet "objet_dumpbd"

    Récupère la liste de tous les genres du film sélectionné par le bouton "MODIFIER" de "personnes_droits_afficher.html"
    
    Dans une liste déroulante particulière (tags-selector-tagselect), on voit :
    1) Tous les genres contenus dans la "t_genre".
    2) Les genres attribués au film selectionné.
    3) Les genres non-attribués au film sélectionné.

    On signale les erreurs importantes

"""


@obj_mon_application.route("/edit_droit_selected", methods=['GET', 'POST'])
def edit_droit_selected():
    if request.method == "GET":
        try:
            with MaBaseDeDonnee().connexion_bd.cursor() as mc_afficher:
                strsql_droits_afficher = """SELECT id_droit, droit FROM t_droit ORDER BY id_droit ASC"""
                mc_afficher.execute(strsql_droits_afficher)
            data_droits_all = mc_afficher.fetchall()
            print("dans edit_droit_selected ---> data_droits_all", data_droits_all)

            # Récupère la valeur de "id_film" du formulaire html "personnes_droits_afficher.html"
            # l'utilisateur clique sur le bouton "Modifier" et on récupère la valeur de "id_film"
            # grâce à la variable "id_film_genres_edit_html" dans le fichier "personnes_droits_afficher.html"
            # href="{{ url_for('edit_genre_film_selected', id_film_genres_edit_html=row.id_film) }}"
            id_droits_edit = request.values['id_personne_droits_edit_html']

            # Mémorise l'id du film dans une variable de session
            # (ici la sécurité de l'application n'est pas engagée)
            # il faut éviter de stocker des données sensibles dans des variables de sessions.
            session['session_id_droits_edit'] = id_droits_edit

            # Constitution d'un dictionnaire pour associer l'id du film sélectionné avec un nom de variable
            valeur_id_droit_selected_dictionnaire = {"value_id_droit_selected": id_droits_edit}

            # Récupère les données grâce à 3 requêtes MySql définie dans la fonction genres_films_afficher_data
            # 1) Sélection du film choisi
            # 2) Sélection des genres "déjà" attribués pour le film.
            # 3) Sélection des genres "pas encore" attribués pour le film choisi.
            # ATTENTION à l'ordre d'assignation des variables retournées par la fonction "genres_films_afficher_data"
            data_droit_selected, data_droits_non_attribues, data_droits_attribues = \
                droits_personnes_afficher_data(valeur_id_droit_selected_dictionnaire)

            print(data_droit_selected)
            lst_droit_selected = [item['id_personne'] for item in data_droit_selected]
            print("lst_data_personne_selected  ", lst_droit_selected,
                  type(lst_droit_selected))

            # Dans le composant "tags-selector-tagselect" on doit connaître
            # les genres qui ne sont pas encore sélectionnés.
            lst_data_droits_non_attribues = [item['id_droit'] for item in data_droits_non_attribues]
            session['session_lst_data_droits_personnes_non_attribues'] = lst_data_droits_non_attribues
            print("lst_data_droits_personnes_non_attribues  ", lst_data_droits_non_attribues,
                  type(lst_data_droits_non_attribues))

            # Dans le composant "tags-selector-tagselect" on doit connaître
            # les genres qui sont déjà sélectionnés.
            lst_data_droits_old_attribues = [item['id_droit'] for item in data_droits_attribues]
            session['session_lst_data_droits_personnes_old_attribues'] = lst_data_droits_old_attribues
            print("lst_data_droits_personnes_old_attribues  ", lst_data_droits_old_attribues,
                  type(lst_data_droits_old_attribues))

            print(" data data_droit_personne_selected", data_droit_selected, "type ", type(data_droit_selected))
            print(" data data_droits_personnes_non_attribues ", data_droits_non_attribues, "type ",
                  type(data_droits_non_attribues))
            print(" data_droits_personnes_attribues ", data_droits_attribues, "type ",
                  type(data_droits_attribues))

            # Extrait les valeurs contenues dans la table "t_genres", colonne "droit"
            # Le composant javascript "tagify" pour afficher les tags n'a pas besoin de l'id_genre
            lst_data_droits_non_attribues = [item['droit'] for item in data_droits_non_attribues]
            print("lst_all_droits gf_edit_droit_personne_selected ", lst_data_droits_non_attribues,
                  type(lst_data_droits_non_attribues))

        except Exception as Exception_edit_droit_selected:
            code, msg = Exception_edit_droit_selected.args
            flash(f"{error_codes.get(code, msg)} ", "danger")
            flash(f"Exception edit_droit_selected : {sys.exc_info()[0]} "
                  f"{Exception_edit_droit_selected.args[0]} , "
                  f"{Exception_edit_droit_selected}", "danger")

    return render_template("droits/droits_modifier_tags_dropbox.html",
                           data_droits=data_droits_all,
                           data_personne_selected=data_droit_selected,
                           data_droits_attribues=data_droits_attribues,
                           data_droits_non_attribues=data_droits_non_attribues)


"""
    nom: update_genre_film_selected

    Récupère la liste de tous les genres du film sélectionné par le bouton "MODIFIER" de "personnes_droits_afficher.html"
    
    Dans une liste déroulante particulière (tags-selector-tagselect), on voit :
    1) Tous les genres contenus dans la "t_genre".
    2) Les genres attribués au film selectionné.
    3) Les genres non-attribués au film sélectionné.

    On signale les erreurs importantes
"""


@obj_mon_application.route("/update_droit_personne_selected", methods=['GET', 'POST'])
def update_droit_personne_selected():
    if request.method == "POST":
        try:
            # Récupère l'id du film sélectionné
            id_personne_selected = session['session_id_droits_edit']
            print("session['session_id_droits_edit'] ", session['session_id_droits_edit'])

            # Récupère la liste des genres qui ne sont pas associés au film sélectionné.
            old_lst_data_droits_non_attribues = session['session_lst_data_droits_non_attribues']
            print("old_lst_data_droits_non_attribues ", old_lst_data_droits_non_attribues)

            # Récupère la liste des genres qui sont associés au film sélectionné.
            old_lst_data_droits_attribues = session['session_lst_data_droits_old_attribues']
            print("old_lst_data_droits_old_attribues ", old_lst_data_droits_attribues)

            # Effacer toutes les variables de session.
            session.clear()

            # Récupère ce que l'utilisateur veut modifier comme genres dans le composant "tags-selector-tagselect"
            # dans le fichier "genres_films_modifier_tags_dropbox.html"
            new_lst_str_droits = request.form.getlist('name_select_tags')
            print("new_lst_str_droits ", new_lst_str_droits)

            # OM 2021.05.02 Exemple : Dans "name_select_tags" il y a ['4','65','2']
            # On transforme en une liste de valeurs numériques. [4,65,2]
            new_lst_int_droit_old = list(map(int, new_lst_str_droits))
            print("new_lst_droit ", new_lst_int_droit_old, "type new_lst_droit ",
                  type(new_lst_int_droit_old))

            # Pour apprécier la facilité de la vie en Python... "les ensembles en Python"
            # https://fr.wikibooks.org/wiki/Programmation_Python/Ensembles
            # OM 2021.05.02 Une liste de "id_genre" qui doivent être effacés de la table intermédiaire "t_genre_film".
            lst_diff_droits_delete_b = list(
                set(old_lst_data_droits_attribues) - set(new_lst_int_droit_old))
            print("lst_diff_droits_delete_b ", lst_diff_droits_delete_b)

            # Une liste de "id_genre" qui doivent être ajoutés à la "t_genre_film"
            lst_diff_droits_insert_a = list(
                set(new_lst_int_droit_old) - set(old_lst_data_droits_attribues))
            print("lst_diff_droits_insert_a ", lst_diff_droits_insert_a)

            # SQL pour insérer une nouvelle association entre
            # "fk_film"/"id_film" et "fk_genre"/"id_genre" dans la "t_genre_film"
            strsql_insert_droit_personne = """INSERT INTO t_avoir_droit (id_avoir_droit, fk_droit, fk_personne)
                                                    VALUES (NULL, %(value_fk_droit)s, %(value_fk_personne)s)"""

            # SQL pour effacer une (des) association(s) existantes entre "id_film" et "id_genre" dans la "t_genre_film"
            strsql_delete_droit_personne = """DELETE FROM t_avoir_droit WHERE fk_droit = %(value_fk_droit)s AND fk_personne = %(value_fk_personne)s"""

            with MaBaseDeDonnee() as mconn_bd:
                # Pour le film sélectionné, parcourir la liste des genres à INSÉRER dans la "t_genre_film".
                # Si la liste est vide, la boucle n'est pas parcourue.
                for id_droit_ins in lst_diff_droits_insert_a:
                    # Constitution d'un dictionnaire pour associer l'id du film sélectionné avec un nom de variable
                    # et "id_genre_ins" (l'id du genre dans la liste) associé à une variable.
                    valeurs_personne_sel_droit_sel_dictionnaire = {"value_fk_personne": id_personne_selected,
                                                               "value_fk_droit": id_droit_ins}

                    mconn_bd.mabd_execute(strsql_insert_droit_personne, valeurs_personne_sel_droit_sel_dictionnaire)

                # Pour le film sélectionné, parcourir la liste des genres à EFFACER dans la "t_genre_film".
                # Si la liste est vide, la boucle n'est pas parcourue.
                for id_droit_del in lst_diff_droits_delete_b:
                    # Constitution d'un dictionnaire pour associer l'id du film sélectionné avec un nom de variable
                    # et "id_genre_del" (l'id du genre dans la liste) associé à une variable.
                    valeurs_personne_sel_droit_sel_dictionnaire = {"value_fk_persone": id_personne_selected,
                                                               "value_fk_droit": id_droit_del}

                    # Du fait de l'utilisation des "context managers" on accède au curseur grâce au "with".
                    # la subtilité consiste à avoir une méthode "mabd_execute" dans la classe "MaBaseDeDonnee"
                    # ainsi quand elle aura terminé l'insertion des données le destructeur de la classe "MaBaseDeDonnee"
                    # sera interprété, ainsi on fera automatiquement un commit
                    mconn_bd.mabd_execute(strsql_delete_droit_personne, valeurs_personne_sel_droit_sel_dictionnaire)

        except Exception as Exception_update_droit_personne_selected:
            code, msg = Exception_update_droit_personne_selected.args
            flash(f"{error_codes.get(code, msg)} ", "danger")
            flash(f"Exception update_droit_personne_selected : {sys.exc_info()[0]} "
                  f"{Exception_update_droit_personne_selected.args[0]} , "
                  f"{Exception_update_droit_personne_selected}", "danger")

    # Après cette mise à jour de la table intermédiaire "t_genre_film",
    # on affiche les films et le(urs) genre(s) associé(s).
    return redirect(url_for('personnes_droits_afficher', id_personne_sel=id_personne_selected))


"""
    nom: genres_films_afficher_data

    Récupère la liste de tous les genres du film sélectionné par le bouton "MODIFIER" de "personnes_droits_afficher.html"
    Nécessaire pour afficher tous les "TAGS" des genres, ainsi l'utilisateur voit les genres à disposition

    On signale les erreurs importantes
"""


def droits_personnes_afficher_data(valeur_id_personne_selected_dict):
    print("valeur_id_personne_selected_dict...", valeur_id_personne_selected_dict)
    try:

        strsql_personne_selected = """SELECT id_personne, Nom_personne, Prenom_personne, Date_naissance_personne, Adresse_mail_personne, MDP_personne, GROUP_CONCAT(id_droit) as DroitsPersonnes FROM t_avoir_droit
                                        INNER JOIN t_personne ON t_personne.id_personne = t_avoir_droit.fk_personne
                                        INNER JOIN t_droit ON t_droit.id_droit = t_avoir_personne.fk_droit
                                        WHERE id_personne = %(value_id_personne_selected)s"""

        strsql_droits_personnes_non_attribues = """SELECT id_droit, droit FROM t_droit WHERE id_droit not in(SELECT id_droit as idDroitsPersonnes FROM t_avoir_droit
                                                    INNER JOIN t_personne ON t_personne.id_personne = t_avoir_droit.fk_personne
                                                    INNER JOIN t_droit ON t_droit.id_droit = t_avoir_droit.fk_droit
                                                    WHERE id_personne = %(value_id_personne_selected)s)"""

        strsql_droits_personnes_attribues = """SELECT id_personne, id_droit, droit FROM t_avoir_droit
                                            INNER JOIN t_personne ON t_personne.id_personne = t_avoir_droit.fk_personne
                                            INNER JOIN t_personne ON t_personne.id_personne = t_avoir_droit.fk_droit
                                            WHERE id_personne = %(value_id_personne_selected)s"""

        # Du fait de l'utilisation des "context managers" on accède au curseur grâce au "with".
        with MaBaseDeDonnee().connexion_bd.cursor() as mc_afficher:
            # Envoi de la commande MySql
            mc_afficher.execute(strsql_droits_personnes_non_attribues, valeur_id_personne_selected_dict)
            # Récupère les données de la requête.
            data_droits_personnes_non_attribues = mc_afficher.fetchall()
            # Affichage dans la console
            print("droits_personnes_afficher_data ----> data_droits_personnes_non_attribues ", data_droits_personnes_non_attribues,
                  " Type : ",
                  type(data_droits_personnes_non_attribues))

            # Envoi de la commande MySql
            mc_afficher.execute(strsql_personne_selected, valeur_id_personne_selected_dict)
            # Récupère les données de la requête.
            data_personne_selected = mc_afficher.fetchall()
            # Affichage dans la console
            print("data_personne_selected  ", data_personne_selected, " Type : ", type(data_personne_selected))

            # Envoi de la commande MySql
            mc_afficher.execute(strsql_droits_personnes_attribues, valeur_id_personne_selected_dict)
            # Récupère les données de la requête.
            data_droits_personnes_attribues = mc_afficher.fetchall()
            # Affichage dans la console
            print("data_droits_personnes_attribues ", data_droits_personnes_attribues, " Type : ",
                  type(data_droits_personnes_attribues))

            # Retourne les données des "SELECT"
            return data_personne_selected, data_droits_personnes_non_attribues, data_droits_personnes_attribues
    except pymysql.Error as pymysql_erreur:
        code, msg = pymysql_erreur.args
        flash(f"{error_codes.get(code, msg)} ", "danger")
        flash(f"pymysql.Error Erreur dans droits_personnes_afficher_data : {sys.exc_info()[0]} "
              f"{pymysql_erreur.args[0]} , "
              f"{pymysql_erreur}", "danger")
    except Exception as exception_erreur:
        code, msg = exception_erreur.args
        flash(f"{error_codes.get(code, msg)} ", "danger")
        flash(f"Exception Erreur dans droits_personnes_afficher_data : {sys.exc_info()[0]} "
              f"{exception_erreur.args[0]} , "
              f"{exception_erreur}", "danger")
    except pymysql.err.IntegrityError as IntegrityError_droits_personnes_afficher_data:
        code, msg = IntegrityError_droits_personnes_afficher_data.args
        flash(f"{error_codes.get(code, msg)} ", "danger")
        flash(f"pymysql.err.IntegrityError Erreur dans droits_personnes_afficher_data : {sys.exc_info()[0]} "
              f"{IntegrityError_droits_personnes_afficher_data.args[0]} , "
              f"{IntegrityError_droits_personnes_afficher_data}", "danger")



"""
    Auteur : OM 2021.03.22
    Définition d'une "route" /personnes_ajouter
    
    Test : ex : http://127.0.0.1:5005/personnes_ajouter
    
    Paramètres : sans
    
    But : Ajouter un contenu pour un film
    
    Remarque :  Dans le champ "name_contenu_html" du formulaire "contenus/personnes_ajouter.html",
                le contrôle de la saisie s'effectue ici en Python.
                On transforme la saisie en minuscules.
                On ne doit pas accepter des valeurs vides, des valeurs avec des chiffres,
                des valeurs avec des caractères qui ne sont pas des lettres.
                Pour comprendre [A-Za-zÀ-ÖØ-öø-ÿ] il faut se reporter à la table ASCII https://www.ascii-code.com/
                Accepte le trait d'union ou l'apostrophe, et l'espace entre deux mots, mais pas plus d'une occurence.
"""





@obj_mon_application.route("/personnes_ajouter", methods=['GET', 'POST'])
def personnes_ajouter_wtf():
    form = FormWTFAjouterpersonnes()
    if request.method == "POST":
        try:
            try:
                # Renvoie une erreur si la connexion est perdue.
                MaBaseDeDonnee().connexion_bd.ping(False)
            except Exception as erreur:
                flash(f"Dans Gestion contenus ...terrible erreur, il faut connecter une base de donnée", "danger")
                print(f"Exception grave Classe constructeur Gestioncontenus {erreur.args[0]}")
                raise MaBdErreurConnexion(f"{msg_erreurs['ErreurConnexionBD']['message']} {erreur.args[0]}")

            if form.validate_on_submit():
                nom_nompersonne_wtf = form.nom_nompersonne_wtf.data
                nom_prenompersonne_wtf = form.nom_prenompersonne_wtf.data
                nom_datepersonne_wtf = form.nom_datepersonne_wtf.data
                adressemailpersonne_wtf = form.adressemailpersonne_wtf.data
                nom_mdppersonne_wtf = form.nom_mdppersonne_wtf.data


                valeurs_insertion_dictionnaire = {"value_Nom_personne": nom_nompersonne_wtf,
                                                  "value_Prenom_personne": nom_prenompersonne_wtf,
                                                  "value_date_personne": nom_datepersonne_wtf,
                                                  "value_adressemail_personne": adressemailpersonne_wtf,
                                                  "value_MDP_personne": nom_mdppersonne_wtf}
                print("valeurs_insertion_dictionnaire ", valeurs_insertion_dictionnaire)

                strsql_insert_personne = """INSERT INTO t_personne (Id_personne, Nom_personne, Prenom_personne, Date_naissance_personne, MDP_personne) VALUES (NULL,%(value_Nom_personne)s), (NULL,%(value_Prenom_personne)s), (NULL,%(value_date_personne)s), (NULL,%(value_adressemail_personne)s), (NULL,%(value_MDP_personne)s)"""
                with MaBaseDeDonnee() as mconn_bd:
                    mconn_bd.mabd_execute(strsql_insert_personne, valeurs_insertion_dictionnaire)


                flash(f"Données insérées !!", "success")
                print(f"Données insérées !!")

                # Pour afficher et constater l'insertion de la valeur, on affiche en ordre inverse. (DESC)
                return redirect(url_for('personnes_afficher', order_by='DESC', id_personne_sel=1))

        # ATTENTION à l'ordre des excepts, il est très important de respecter l'ordre.
        except pymysql.err.IntegrityError as erreur_personne_doublon:
            # Dérive "pymysql.err.IntegrityError" dans "MaBdErreurDoublon" fichier "erreurs/exceptions.py"
            # Ainsi on peut avoir un message d'erreur personnalisé.
            code, msg = erreur_personne_doublon.args

            flash(f"{error_codes.get(code, msg)} ", "warning")

        # OM 2020.04.16 ATTENTION à l'ordre des excepts, il est très important de respecter l'ordre.
        except (pymysql.err.OperationalError,
                pymysql.ProgrammingError,
                pymysql.InternalError,
                TypeError) as erreur_gest_genr_crud:
            code, msg = erreur_gest_genr_crud.args

            flash(f"{error_codes.get(code, msg)} ", "danger")
            flash(f"Erreur dans Gestion personnes CRUD : {sys.exc_info()[0]} "
                  f"{erreur_gest_genr_crud.args[0]} , "
                  f"{erreur_gest_genr_crud}", "danger")

    return render_template("droits/personnes_ajouter_wtf.html", form=form)







"""
    Auteur : OM 2021.03.29
    Définition d'une "route" /contenu_update
    
    Test : ex cliquer sur le menu "contenus" puis cliquer sur le bouton "EDIT" d'un "contenu"
    
    Paramètres : sans
    
    But : Editer(update) un contenu qui a été sélectionné dans le formulaire "contenus_afficher.html"
    
    Remarque :  Dans le champ "nom_contenu_update_wtf" du formulaire "contenus/contenu_update_wtf.html",
                le contrôle de la saisie s'effectue ici en Python.
                On transforme la saisie en minuscules.
                On ne doit pas accepter des valeurs vides, des valeurs avec des chiffres,
                des valeurs avec des caractères qui ne sont pas des lettres.
                Pour comprendre [A-Za-zÀ-ÖØ-öø-ÿ] il faut se reporter à la table ASCII https://www.ascii-code.com/
                Accepte le trait d'union ou l'apostrophe, et l'espace entre deux mots, mais pas plus d'une occurence.
"""


@obj_mon_application.route("/personne_update", methods=['GET', 'POST'])
def personne_update_wtf():

    # L'utilisateur vient de cliquer sur le bouton "EDIT". Récupère la valeur de "id_contenu"
    id_personne_update = request.values['id_personne_btn_edit_html']

    # Objet formulaire pour l'UPDATE
    form_update = FormWTFUpdatePersonne()
    try:
        print(" on submit ", form_update.validate_on_submit())
        if form_update.validate_on_submit():
            # Récupèrer la valeur du champ depuis "contenu_update_wtf.html" après avoir cliqué sur "SUBMIT".
            # Puis la convertir en lettres minuscules.
            nom_nompersonne_update_wtf = form_update.nom_nompersonne_update_wtf.data
            nom_prenompersonne_update_wtf = form_update.nom_prenompersonne_update_wtf.data
            nom_datepersonne_update_wtf = form_update.nom_datepersonne_update_wtf.data
            adressemailpersonne_update_wtf = form_update.adressemailpersonne_update_wtf.data
            nom_mdppersonne_update_wtf = form_update.nom_mdppersonne_update_wtf.data

            valeur_update_dictionnaire = {"value_personne": id_personne_update,
                                          "value_Nom_personne": nom_nompersonne_update_wtf,
                                          "value_Prenom_personne": nom_prenompersonne_update_wtf,
                                          "value_date_personne": nom_datepersonne_update_wtf,
                                          "value_adressemail_personne": adressemailpersonne_update_wtf,
                                          "value_MDP_personne": nom_mdppersonne_update_wtf}
            print("valeur_update_dictionnaire ", valeur_update_dictionnaire)

            str_sql_update_personne = """UPDATE t_personne SET Nom_personne = %(value_Nom_personne)s, Prenom_personne = %(value_Prenom_personne)s, Date_naissance_personne = %(value_date_personne)s, Adresse_mail_personne = %(value_adressemail_personne)s, MDP_personne = %(value_MDP_personne)s,0) WHERE id_personne = %(value_personne)s"""
            with MaBaseDeDonnee() as mconn_bd:
                mconn_bd.mabd_execute(str_sql_update_personne, valeur_update_dictionnaire)

            flash(f"Donnée mise à jour !!", "success")
            print(f"Donnée mise à jour !!")

            # afficher et constater que la donnée est mise à jour.
            # Affiche seulement la valeur modifiée, "ASC" et l'"id_contenu_update"
            return redirect(url_for('personnes_afficher', order_by="ASC", id_personne_sel=id_personne_update))
        elif request.method == "GET":
            # Opération sur la BD pour récupérer "id_contenu" et "contenu" de la "t_contenu"
            str_sql_id_personne = "SELECT id_personne, Nom_personne, Prenom_personne, Date_naissance_personne, Adresse_mail_personne, MDP_personne FROM t_personne WHERE id_personne = %(value_personne)s"
            valeur_select_dictionnaire = {"id_personne_btn_edit_html": id_personne_update}
            mybd_curseur = MaBaseDeDonnee().connexion_bd.cursor()
            mybd_curseur.execute(str_sql_id_personne, valeur_select_dictionnaire)
            # Une seule valeur est suffisante "fetchone()", vu qu'il n'y a qu'un seul champ "nom contenu" pour l'UPDATE
            data_nom_personne = mybd_curseur.fetchone()
            print("  ", data_nom_personne, " type ", type(data_nom_personne), " personne ",
                  data_nom_personne["Nom_personne"])

            # Afficher la valeur sélectionnée dans le champ du formulaire "contenu_update_wtf.html"
            form_update.nom_nompersonne_update_wtf.data = data_nom_personne["Nom_personne"]
            form_update.nom_prenompersonne_update_wtf.data = data_nom_personne["Prenom_personne"]
            form_update.nom_datepersonne_update_wtf.data = data_nom_personne["Date_naissance_personne"]
            form_update.adressemailpersonne_update_wtf.data = data_nom_personne["Adresse_mail_personne"]
            form_update.nom_mdppersonne_update_wtf.data = data_nom_personne["MDP_personne"]
    # OM 2020.04.16 ATTENTION à l'ordre des excepts, il est très important de respecter l'ordre.
    except KeyError:
        flash(f"__KeyError dans personne_update_wtf : {sys.exc_info()[0]} {sys.exc_info()[1]} {sys.exc_info()[2]}",
              "danger")
    except ValueError:
        flash(f"Erreur dans personne_update_wtf : {sys.exc_info()[0]} {sys.exc_info()[1]}", "danger")
    except (pymysql.err.OperationalError,
            pymysql.ProgrammingError,
            pymysql.InternalError,
            pymysql.err.IntegrityError,
            TypeError) as erreur_gest_genr_crud:
        code, msg = erreur_gest_genr_crud.args
        flash(f"attention : {error_codes.get(code, msg)} {erreur_gest_genr_crud} ", "danger")
        flash(f"Erreur dans personne_update_wtf : {sys.exc_info()[0]} "
              f"{erreur_gest_genr_crud.args[0]} , "
              f"{erreur_gest_genr_crud}", "danger")
        flash(f"__KeyError dans personne_update_wtf : {sys.exc_info()[0]} {sys.exc_info()[1]} {sys.exc_info()[2]}",
              "danger")

    return render_template("droits/personne_update_wtf.html", form_update=form_update)


"""
    Auteur : OM 2021.04.08
    Définition d'une "route" /contenu_delete
    
    Test : ex. cliquer sur le menu "contenus" puis cliquer sur le bouton "DELETE" d'un "contenu"
    
    Paramètres : sans
    
    But : Effacer(delete) un contenu qui a été sélectionné dans le formulaire "contenus_afficher.html"
    
    Remarque :  Dans le champ "nom_contenu_delete_wtf" du formulaire "contenus/contenu_delete_wtf.html",
                le contrôle de la saisie est désactivée. On doit simplement cliquer sur "DELETE"
"""


@obj_mon_application.route("/personne_delete", methods=['GET', 'POST'])
def personne_delete_wtf():
    data_armoirs_attribue_personne_delete = None
    btn_submit_del = None
    # L'utilisateur vient de cliquer sur le bouton "DELETE". Récupère la valeur de "id_contenu"
    id_personne_delete = request.values['id_personne_btn_delete_html']

    # Objet formulaire pour effacer le contenu sélectionné.
    form_delete = FormWTFDeletepersonne()
    try:
        print(" on submit ", form_delete.validate_on_submit())
        if request.method == "POST" and form_delete.validate_on_submit():

            if form_delete.submit_btn_annuler.data:
                return redirect(url_for("personnes_afficher", order_by="ASC", id_personne_sel=0))

            if form_delete.submit_btn_conf_del.data:
                # Récupère les données afin d'afficher à nouveau
                # le formulaire "contenus/contenu_delete_wtf.html" lorsque le bouton "Etes-vous sur d'effacer ?" est cliqué.
                data_armoirs_attribue_personne_delete = session['data_armoirs_attribue_personne_delete']
                print("data_armoirs_attribue_personne_delete ", data_armoirs_attribue_personne_delete)

                flash(f"Effacer le contenu de façon définitive de la BD !!!", "danger")
                # L'utilisateur vient de cliquer sur le bouton de confirmation pour effacer...
                # On affiche le bouton "Effacer contenu" qui va irrémédiablement EFFACER le contenu
                btn_submit_del = True

            if form_delete.submit_btn_del.data:
                valeur_delete_dictionnaire = {"value_id_personne": id_personne_delete}
                print("valeur_delete_dictionnaire ", valeur_delete_dictionnaire)

                str_sql_delete_personnes_personne = """DELETE FROM t_avoir_droit WHERE Fk_personne = %(value_id_personne)s"""
                str_sql_delete_idpersonne= """DELETE FROM t_personne WHERE id_personne = %(value_id_personne)s"""
                # Manière brutale d'effacer d'abord la "Fk_contenu", même si elle n'existe pas dans la "t_avoir_contenu"
                # Ensuite on peut effacer le contenu vu qu'il n'est plus "lié" (INNODB) dans la "t_avoir_contenu"
                with MaBaseDeDonnee() as mconn_bd:
                    mconn_bd.mabd_execute(str_sql_delete_personnes_personne, valeur_delete_dictionnaire)
                    mconn_bd.mabd_execute(str_sql_delete_idpersonne, valeur_delete_dictionnaire)

                flash(f"personne définitivement effacé !!", "success")
                print(f"personne définitivement effacé !!")

                # afficher les données
                return redirect(url_for('personnes_afficher', order_by="ASC", id_personne_sel=0))

        if request.method == "GET":
            valeur_select_dictionnaire = {"value_id_personne": id_personne_delete}
            print(id_personne_delete, type(id_personne_delete))



            mybd_curseur = MaBaseDeDonnee().connexion_bd.cursor()

            data_armoirs_attribue_personne_delete = mybd_curseur.fetchall()
            print("data_armoirs_attribue_personne_delete...", data_armoirs_attribue_personne_delete)

            # Nécessaire pour mémoriser les données afin d'afficher à nouveau
            # le formulaire "personnes/personne_delete_wtf.html" lorsque le bouton "Etes-vous sur d'effacer ?" est cliqué.
            session['data_armoirs_attribue_personne_delete'] = data_armoirs_attribue_personne_delete

            # Opération sur la BD pour récupérer "id_contenu" et "contenu" de la "t_contenu"
            str_sql_id_personne = "SELECT t_personne.id_personne, t_personne.Nom_personne, t_personne.Prenom_personne, t_personne.Date_naissance_personne, t_personne.Adresse_mail_personne, t_personne.MDP_personne WHERE id_personne = %(value_id_personne)s"

            mybd_curseur.execute(str_sql_id_personne, valeur_select_dictionnaire)
            # Une seule valeur est suffisante "fetchone()",
            # vu qu'il n'y a qu'un seul champ "nom contenu" pour l'action DELETE
            data_personne = mybd_curseur.fetchone()
            print("data_personne ", data_personne, " type ", type(data_personne), " personne ",
                  data_personne["contenu"])

            # Afficher la valeur sélectionnée dans le champ du formulaire "contenu_delete_wtf.html"
            form_delete.nom_personne_delete_wtf.data = data_personne["personne"]

            # Le bouton pour l'action "DELETE" dans le form. "contenu_delete_wtf.html" est caché.
            btn_submit_del = False

    # OM 2020.04.16 ATTENTION à l'ordre des excepts, il est très important de respecter l'ordre.
    except KeyError:
        flash(f"__KeyError dans personne_delete_wtf : {sys.exc_info()[0]} {sys.exc_info()[1]} {sys.exc_info()[2]}",
              "danger")
    except ValueError:
        flash(f"Erreur dans personne_delete_wtf : {sys.exc_info()[0]} {sys.exc_info()[1]}", "danger")
    except (pymysql.err.OperationalError,
            pymysql.ProgrammingError,
            pymysql.InternalError,
            pymysql.err.IntegrityError,
            TypeError) as erreur_gest_genr_crud:
        code, msg = erreur_gest_genr_crud.args
        flash(f"attention : {error_codes.get(code, msg)} {erreur_gest_genr_crud} ", "danger")

        flash(f"Erreur dans personne_delete_wtf : {sys.exc_info()[0]} "
              f"{erreur_gest_genr_crud.args[0]} , "
              f"{erreur_gest_genr_crud}", "danger")

        flash(f"__KeyError dans personne_delete_wtf : {sys.exc_info()[0]} {sys.exc_info()[1]} {sys.exc_info()[2]}",
              "danger")

    return render_template("personnes/personne_delete_wtf.html",
                           form_delete=form_delete,
                           btn_submit_del=btn_submit_del,
                           data_films_associes=data_armoirs_attribue_personne_delete)

@obj_mon_application.route("/droit_personne_ajouter", methods=['GET', 'POST'])
def droit_personne_ajouter_wtf():
    form = FormWTFAjouterDetails()
    if request.method == "POST":
        try:
            try:
                # Renvoie une erreur si la connexion est perdue.
                MaBaseDeDonnee().connexion_bd.ping(False)
            except Exception as erreur:
                flash(f"Dans Gestion droits ...terrible erreur, il faut connecter une base de donnée", "danger")
                print(f"Exception grave Classe constructeur Gestiondroits {erreur.args[0]}")
                raise MaBdErreurConnexion(f"{msg_erreurs['ErreurConnexionBD']['message']} {erreur.args[0]}")

            if form.validate_on_submit():
                droit_personne_wtf = form.droit_wtf.data
                droit_personne = droit_personne_wtf.capitalize()


                valeurs_insertion_dictionnaire = {"value_origine": droit_personne}

                print("valeurs_insertion_dictionnaire ", valeurs_insertion_dictionnaire)

                strsql_insert_droit = """INSERT INTO t_droit (id_droit, droit) VALUES (NULL,%(value_droit)s)"""
                with MaBaseDeDonnee() as mconn_bd:
                    mconn_bd.mabd_execute(strsql_insert_droit, valeurs_insertion_dictionnaire)

                flash(f"Données insérées !!", "info")
                print(f"Données insérées !!")
                print(f"Données insérées !!")

                # Pour afficher et constater l'insertion de la valeur, on affiche en ordre inverse. (DESC)
                return redirect(url_for('droit_personnes_afficher', order_by='ASC', id_personne_sel=0))

        # ATTENTION à l'ordre des excepts, il est très important de respecter l'ordre.
        except pymysql.err.IntegrityError as erreur_droit_doublon:
            # Dérive "pymysql.err.IntegrityError" dans "MaBdErreurDoublon" fichier "erreurs/exceptions.py"
            # Ainsi on peut avoir un message d'erreur personnalisé.
            code, msg = erreur_droit_doublon.args

            flash(f"{error_codes.get(code, msg)} ", "warning")

        # OM 2020.04.16 ATTENTION à l'ordre des excepts, il est très important de respecter l'ordre.
        except (pymysql.err.OperationalError,
                pymysql.ProgrammingError,
                pymysql.InternalError,
                TypeError) as erreur_gest_genr_crud:
            code, msg = erreur_gest_genr_crud.args

            flash(f"{error_codes.get(code, msg)} ", "danger")
            flash(f"Erreur dans Gestion genres CRUD : {sys.exc_info()[0]} "
                  f"{erreur_gest_genr_crud.args[0]} , "
                  f"{erreur_gest_genr_crud}", "danger")

    return render_template("Origines_collaborateurs/droit_personne_ajouter.html", form=form)
