"""
    Fichier : gestion_contenus_crud.py
    Auteur : OM 2021.03.16
    Gestions des "routes" FLASK et des données pour les contenus.
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
from APP_FILMS.contenus.gestion_contenus_wtf_forms import FormWTFAjoutercontenus
from APP_FILMS.contenus.gestion_contenus_wtf_forms import FormWTFDeletecontenu
from APP_FILMS.contenus.gestion_contenus_wtf_forms import FormWTFUpdateContenu


"""
    Auteur : OM 2021.03.16
    Définition d'une "route" /contenus_afficher
    
    Test : ex : http://127.0.0.1:5005/contenus_afficher
    
    Paramètres : order_by : ASC : Ascendant, DESC : Descendant
                id_contenu_sel = 0 >> tous les contenus.
                id_contenu_sel = "n" affiche le contenu dont l'id est "n"
"""


@obj_mon_application.route("/contenus_afficher/<string:order_by>/<int:id_contenu_sel>", methods=['GET', 'POST'])
def contenus_afficher(order_by, id_contenu_sel):
    if request.method == "GET":
        try:
            try:
                # Renvoie une erreur si la connexion est perdue.
                MaBaseDeDonnee().connexion_bd.ping(False)
            except Exception as erreur:
                flash(f"Dans Gestion contenus ...terrible erreur, il faut connecter une base de donnée", "danger")
                print(f"Exception grave Classe constructeur Gestioncontenus {erreur.args[0]}")
                raise MaBdErreurConnexion(f"{msg_erreurs['ErreurConnexionBD']['message']} {erreur.args[0]}")

            with MaBaseDeDonnee().connexion_bd.cursor() as mc_afficher:
                if order_by == "ASC" and id_contenu_sel == 0:
                    strsql_contenus_afficher = """SELECT `t_contenu`.`Id_contenu`, `t_contenu`.`contenu`, `t_contenu`.`Nb_contenu`, `t_piece`.`Nom_piece`
                                                        FROM `t_contenu`
                                                        LEFT JOIN `t_avoir_contenu` ON `t_avoir_contenu`.`Fk_contenu` = `t_contenu`.`Id_contenu`
                                                        LEFT JOIN `t_piece` ON `t_avoir_contenu`.`Fk_piece` = `t_piece`.`Id_piece`"""
                    mc_afficher.execute(strsql_contenus_afficher)


                elif order_by == "ASC":
                    # C'EST LA QUE VOUS ALLEZ DEVOIR PLACER VOTRE PROPRE LOGIQUE MySql
                    # la commande MySql classique est "SELECT * FROM t_contenu"
                    # Pour "lever"(raise) une erreur s'il y a des erreurs sur les noms d'attributs dans la table
                    # donc, je précise les champs à afficher
                    # Constitution d'un dictionnaire pour associer l'id du contenu sélectionné avec un nom de variable
                    valeur_id_contenu_selected_dictionnaire = {"value_id_contenu_selected": id_contenu_sel}
                    strsql_contenus_afficher = """SELECT `t_contenu`.`Id_contenu`, `t_contenu`.`contenu`, `t_contenu`.`Nb_contenu`, `t_piece`.`Nom_piece`
                                                        FROM `t_contenu`
                                                        LEFT JOIN `t_avoir_contenu` ON `t_avoir_contenu`.`Fk_contenu` = `t_contenu`.`Id_contenu`
                                                        LEFT JOIN `t_piece` ON `t_avoir_contenu`.`Fk_piece` = `t_piece`.`Id_piece`"""

                    mc_afficher.execute(strsql_contenus_afficher, valeur_id_contenu_selected_dictionnaire)
                else:
                    strsql_contenus_afficher = """SELECT `t_contenu`.`Id_contenu`, `t_contenu`.`contenu`, `t_contenu`.`Nb_contenu`, `t_piece`.`Nom_piece`
                                                        FROM `t_contenu`
                                                        LEFT JOIN `t_avoir_contenu` ON `t_avoir_contenu`.`Fk_contenu` = `t_contenu`.`Id_contenu`
                                                        LEFT JOIN `t_piece` ON `t_avoir_contenu`.`Fk_piece` = `t_piece`.`Id_piece`"""

                    mc_afficher.execute(strsql_contenus_afficher)

                data_contenus = mc_afficher.fetchall()

                print("data_contenus ", data_contenus, " Type : ", type(data_contenus))

                # Différencier les messages si la table est vide.
                if not data_contenus and id_contenu_sel == 0:
                    flash("""La table "t_contenu" est vide. !!""", "warning")
                elif not data_contenus and id_contenu_sel > 0:
                    # Si l'utilisateur change l'id_contenu dans l'URL et que le contenu n'existe pas,
                    flash(f"Le contenu demandé n'existe pas !!", "warning")
                else:
                    # Dans tous les autres cas, c'est que la table "t_contenu" est vide.
                    # OM 2020.04.09 La ligne ci-dessous permet de donner un sentiment rassurant aux utilisateurs.
                    flash(f"Données contenus affichés !!", "success")

        except Exception as erreur:
            print(f"RGG Erreur générale. contenus_afficher")
            # OM 2020.04.09 On dérive "Exception" par le "@obj_mon_application.errorhandler(404)"
            # fichier "run_mon_app.py"
            # Ainsi on peut avoir un message d'erreur personnalisé.
            flash(f"RGG Exception {erreur} contenus_afficher", "danger")
            raise Exception(f"RGG Erreur générale. {erreur}")
            # raise MaBdErreurOperation(f"RGG Exception {msg_erreurs['ErreurNomBD']['message']} {erreur}")

    # Envoie la page "HTML" au serveur.
    return render_template("contenus/contenus_afficher.html", data=data_contenus)


"""
    Auteur : OM 2021.03.22
    Définition d'une "route" /contenus_ajouter
    
    Test : ex : http://127.0.0.1:5005/contenus_ajouter
    
    Paramètres : sans
    
    But : Ajouter un contenu pour un film
    
    Remarque :  Dans le champ "name_contenu_html" du formulaire "contenus/contenus_ajouter.html",
                le contrôle de la saisie s'effectue ici en Python.
                On transforme la saisie en minuscules.
                On ne doit pas accepter des valeurs vides, des valeurs avec des chiffres,
                des valeurs avec des caractères qui ne sont pas des lettres.
                Pour comprendre [A-Za-zÀ-ÖØ-öø-ÿ] il faut se reporter à la table ASCII https://www.ascii-code.com/
                Accepte le trait d'union ou l'apostrophe, et l'espace entre deux mots, mais pas plus d'une occurence.
"""


@obj_mon_application.route("/contenus_ajouter", methods=['GET', 'POST'])
def contenus_ajouter_wtf():
    form = FormWTFAjoutercontenus()

    if request.method == "GET":
        with MaBaseDeDonnee().connexion_bd.cursor() as mc_afficher:
            piece = """SELECT t_piece.Nom_piece, t_piece.Id_piece FROM t_piece ORDER BY Id_piece ASC"""

            mc_afficher.execute(piece)


    if request.method == "POST":
        try:
            try:
                # Renvoie une erreur si la connexion est perdue.
                MaBaseDeDonnee().connexion_bd.ping(False)
            except Exception as erreur:
                flash(f"Dans Gestion contenus...terrible erreur, il faut connecter une base de donnée", "danger")
                print(f"Exception grave Classe constructeur GestionGenres {erreur.args[0]}")
                raise MaBdErreurConnexion(f"{msg_erreurs['ErreurConnexionBD']['message']} {erreur.args[0]}")

            if form.validate_on_submit():
                nom_nbcontenu_wtf = form.nom_nbcontenu_wtf.data
                nom_contenu_wtf = form.nom_contenu_wtf.data
                nom_piece = request.form.get('Nom_piece')


                valeurs_insertion_dictionnaire = {"value_contenu": nom_contenu_wtf,
                                                  "value_Nb_contenu": nom_nbcontenu_wtf,
                                                  "value_Nom_piece": nom_piece}


                strsql_insert_contenu = """INSERT INTO t_contenu (id_contenu,contenu,Nb_contenu) VALUES (NULL,%(value_contenu)s,%(value_Nb_contenu)s"""
                with MaBaseDeDonnee() as mconn_bd:
                    mconn_bd.mabd_execute(strsql_insert_contenu, valeurs_insertion_dictionnaire)
                    mconn_bd.connexion_bd.commit()

                    # Ici, j'essaie de récuperer l'id de la facture que je viens de créer, pour l'associer au destinataire/motif
                    strsql_insert_con = """SELECT `id_contenu` FROM `t_contenu` ORDER BY `id_contenu` DESC LIMIT 1"""
                    with MaBaseDeDonnee().connexion_bd.cursor() as mconn_bd:
                        mconn_bd.execute(strsql_insert_con)
                        id_contenu = mconn_bd.fetchall()
                    print(id_contenu)

                    valeurs_update_fk = {"id_contenu": id_contenu[0]["id_contenu"],
                                         "value_Nom_piece": valeurs_insertion_dictionnaire["value_Nom_piece"]}

                    # Ici, j'essaie de faire la liason de la fk facture et fk destinataire en récuperant la dernière id crée
                    strsql_insert_fk = """INSERT INTO `t_avoir_contenu` (`id_avoir_contenu`, `fk_contenu`, `Fk_piece`) VALUES (NULL, %(id_contenu)s, %(value_piece)s, CURRENT_TIMESTAMP)"""
                    with MaBaseDeDonnee() as mconn_bd:
                        mconn_bd.mabd_execute(strsql_insert_fk,valeurs_update_fk)

                        print("-------------------------------------------------------------------")
                        print("valeurs_update_fk ", valeurs_update_fk)
                        print("-------------------------------------------------------------------")

                flash(f"Données insérées !!", "success")
                print(f"Données insérées !!")

                # Pour afficher et constater l'insertion de la valeur, on affiche en ordre inverse. (DESC)
                return redirect(url_for('contenus_afficher', order_by='DESC', id_genre_sel=0))

        # ATTENTION à l'ordre des excepts, il est très important de respecter l'ordre.
        except pymysql.err.IntegrityError as erreur_genre_doublon:
            # Dérive "pymysql.err.IntegrityError" dans "MaBdErreurDoublon" fichier "erreurs/exceptions.py"
            # Ainsi on peut avoir un message d'erreur personnalisé.
            code, msg = erreur_genre_doublon.args

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

    strsql_insert_contenu = """SELECT t_piece.Nom_piece, t_piece.id_piece FROM t_piece """
    with MaBaseDeDonnee().connexion_bd.cursor() as mconn_bd:
        mconn_bd.execute(strsql_insert_contenu)
        piece = mconn_bd.fetchall()




    return render_template("contenus/contenus_ajouter_wtf.html", form=form, piece=piece)


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


@obj_mon_application.route("/contenu_update", methods=['GET', 'POST'])
def contenu_update_wtf():

    # L'utilisateur vient de cliquer sur le bouton "EDIT". Récupère la valeur de "id_contenu"
    id_contenu_update = request.values['id_contenu_btn_edit_html']

    # Objet formulaire pour l'UPDATE
    form_update = FormWTFUpdateContenu()
    try:
        print(" on submit ", form_update.validate_on_submit())
        if form_update.validate_on_submit():
            # Récupèrer la valeur du champ depuis "contenu_update_wtf.html" après avoir cliqué sur "SUBMIT".
            # Puis la convertir en lettres minuscules.
            name_contenu_update = form_update.nom_contenu_update_wtf.data
            name_contenu_update = name_contenu_update.lower()

            valeur_update_dictionnaire = {"value_id_contenu": id_contenu_update, "value_name_contenu": name_contenu_update}
            print("valeur_update_dictionnaire ", valeur_update_dictionnaire)

            str_sql_update_intitulecontenu = """UPDATE t_contenu SET contenu = %(value_name_contenu)s WHERE id_contenu = %(value_id_contenu)s"""
            with MaBaseDeDonnee() as mconn_bd:
                mconn_bd.mabd_execute(str_sql_update_intitulecontenu, valeur_update_dictionnaire)

            flash(f"Donnée mise à jour !!", "success")
            print(f"Donnée mise à jour !!")

            # afficher et constater que la donnée est mise à jour.
            # Affiche seulement la valeur modifiée, "ASC" et l'"id_contenu_update"
            return redirect(url_for('contenus_afficher', order_by="ASC", id_contenu_sel=id_contenu_update))
        elif request.method == "GET":
            # Opération sur la BD pour récupérer "id_contenu" et "contenu" de la "t_contenu"
            str_sql_id_contenu = """SELECT `t_contenu`.`Id_contenu`, `t_contenu`.`contenu`, `t_avoir_contenu`.`Nb_contenu`, `t_piece`.`Nom_piece`
                                                        FROM `t_contenu`
                                                        LEFT JOIN `t_avoir_contenu` ON `t_avoir_contenu`.`Fk_contenu` = `t_contenu`.`Id_contenu`
                                                        LEFT JOIN `t_piece` ON `t_avoir_contenu`.`Fk_piece` = `t_piece`.`Id_piece`"""
            valeur_select_dictionnaire = {"value_id_contenu": id_contenu_update}
            mybd_curseur = MaBaseDeDonnee().connexion_bd.cursor()
            mybd_curseur.execute(str_sql_id_contenu, valeur_select_dictionnaire)
            # Une seule valeur est suffisante "fetchone()", vu qu'il n'y a qu'un seul champ "nom contenu" pour l'UPDATE
            data_contenu = mybd_curseur.fetchone()
            print("data_contenu ", data_contenu, " type ", type(data_contenu), " contenu ",
                  data_contenu["contenu"])

            # Afficher la valeur sélectionnée dans le champ du formulaire "contenu_update_wtf.html"
            form_update.nom_contenu_update_wtf.data = data_contenu["contenu"]

    # OM 2020.04.16 ATTENTION à l'ordre des excepts, il est très important de respecter l'ordre.
    except KeyError:
        flash(f"__KeyError dans contenu_update_wtf : {sys.exc_info()[0]} {sys.exc_info()[1]} {sys.exc_info()[2]}",
              "danger")
    except ValueError:
        flash(f"Erreur dans contenu_update_wtf : {sys.exc_info()[0]} {sys.exc_info()[1]}", "danger")
    except (pymysql.err.OperationalError,
            pymysql.ProgrammingError,
            pymysql.InternalError,
            pymysql.err.IntegrityError,
            TypeError) as erreur_gest_genr_crud:
        code, msg = erreur_gest_genr_crud.args
        flash(f"attention : {error_codes.get(code, msg)} {erreur_gest_genr_crud} ", "danger")
        flash(f"Erreur dans contenu_update_wtf : {sys.exc_info()[0]} "
              f"{erreur_gest_genr_crud.args[0]} , "
              f"{erreur_gest_genr_crud}", "danger")
        flash(f"__KeyError dans contenu_update_wtf : {sys.exc_info()[0]} {sys.exc_info()[1]} {sys.exc_info()[2]}",
              "danger")

    return render_template("contenus/contenu_ajouter_wtf.html", form_update=form_update)


"""
    Auteur : OM 2021.04.08
    Définition d'une "route" /contenu_delete
    
    Test : ex. cliquer sur le menu "contenus" puis cliquer sur le bouton "DELETE" d'un "contenu"
    
    Paramètres : sans
    
    But : Effacer(delete) un contenu qui a été sélectionné dans le formulaire "contenus_afficher.html"
    
    Remarque :  Dans le champ "nom_contenu_delete_wtf" du formulaire "contenus/contenu_delete_wtf.html",
                le contrôle de la saisie est désactivée. On doit simplement cliquer sur "DELETE"
"""


@obj_mon_application.route("/contenu_delete", methods=['GET', 'POST'])
def contenu_delete_wtf():
    data_armoirs_attribue_contenu_delete = None
    btn_submit_del = None
    # L'utilisateur vient de cliquer sur le bouton "DELETE". Récupère la valeur de "id_contenu"
    id_contenu_delete = request.values['id_contenu_btn_delete_html']

    # Objet formulaire pour effacer le contenu sélectionné.
    form_delete = FormWTFDeletecontenu()
    try:
        print(" on submit ", form_delete.validate_on_submit())
        if request.method == "POST" and form_delete.validate_on_submit():

            if form_delete.submit_btn_annuler.data:
                return redirect(url_for("contenus_afficher", order_by="ASC", id_contenu_sel=0))

            if form_delete.submit_btn_conf_del.data:
                # Récupère les données afin d'afficher à nouveau
                # le formulaire "contenus/contenu_delete_wtf.html" lorsque le bouton "Etes-vous sur d'effacer ?" est cliqué.
                data_armoirs_attribue_contenu_delete = session['data_armoirs_attribue_contenu_delete']
                print("data_armoirs_attribue_contenu_delete ", data_armoirs_attribue_contenu_delete)

                flash(f"Effacer le contenu de façon définitive de la BD !!!", "danger")
                # L'utilisateur vient de cliquer sur le bouton de confirmation pour effacer...
                # On affiche le bouton "Effacer contenu" qui va irrémédiablement EFFACER le contenu
                btn_submit_del = True

            if form_delete.submit_btn_del.data:
                valeur_delete_dictionnaire = {"value_id_contenu": id_contenu_delete}
                print("valeur_delete_dictionnaire ", valeur_delete_dictionnaire)

                str_sql_delete_contenus_contenu = """DELETE FROM t_avoir_contenu WHERE Fk_contenu = %(value_id_contenu)s; DELETE FROM t_avoir_contenu WHERE Fk_piece = %(value_id_contenu)s"""
                str_sql_delete_idcontenu = """DELETE FROM t_contenu WHERE id_contenu = %(value_id_contenu)s"""
                # Manière brutale d'effacer d'abord la "Fk_contenu", même si elle n'existe pas dans la "t_avoir_contenu"
                # Ensuite on peut effacer le contenu vu qu'il n'est plus "lié" (INNODB) dans la "t_avoir_contenu"
                with MaBaseDeDonnee() as mconn_bd:
                    mconn_bd.mabd_execute(str_sql_delete_contenus_contenu, valeur_delete_dictionnaire)
                    mconn_bd.mabd_execute(str_sql_delete_idcontenu, valeur_delete_dictionnaire)

                flash(f"contenu définitivement effacé !!", "success")
                print(f"contenu définitivement effacé !!")

                # afficher les données
                return redirect(url_for('contenus_afficher', order_by="ASC", id_contenu_sel=0))

        if request.method == "GET":
            valeur_select_dictionnaire = {"value_id_contenu": id_contenu_delete}
            print(id_contenu_delete, type(id_contenu_delete))



            mybd_curseur = MaBaseDeDonnee().connexion_bd.cursor()

            data_armoirs_attribue_contenu_delete = mybd_curseur.fetchall()
            print("data_armoirs_attribue_contenu_delete...", data_armoirs_attribue_contenu_delete)

            # Nécessaire pour mémoriser les données afin d'afficher à nouveau
            # le formulaire "contenus/contenu_delete_wtf.html" lorsque le bouton "Etes-vous sur d'effacer ?" est cliqué.
            session['data_armoirs_attribue_contenu_delete'] = data_armoirs_attribue_contenu_delete

            # Opération sur la BD pour récupérer "id_contenu" et "contenu" de la "t_contenu"
            str_sql_id_contenu = "SELECT t_contenu.id_contenu, t_contenu.contenu, t_avoir_contenu.Nb_contenu, t_piece.Nom_piece FROM t_contenu, t_avoir_contenu, t_piece WHERE id_contenu = %(value_id_contenu)s"

            mybd_curseur.execute(str_sql_id_contenu, valeur_select_dictionnaire)
            # Une seule valeur est suffisante "fetchone()",
            # vu qu'il n'y a qu'un seul champ "nom contenu" pour l'action DELETE
            data_contenu = mybd_curseur.fetchone()
            print("data_contenu ", data_contenu, " type ", type(data_contenu), " contenu ",
                  data_contenu["contenu"])

            # Afficher la valeur sélectionnée dans le champ du formulaire "contenu_delete_wtf.html"
            form_delete.nom_contenu_delete_wtf.data = data_contenu["contenu"]

            # Le bouton pour l'action "DELETE" dans le form. "contenu_delete_wtf.html" est caché.
            btn_submit_del = False

    # OM 2020.04.16 ATTENTION à l'ordre des excepts, il est très important de respecter l'ordre.
    except KeyError:
        flash(f"__KeyError dans contenu_delete_wtf : {sys.exc_info()[0]} {sys.exc_info()[1]} {sys.exc_info()[2]}",
              "danger")
    except ValueError:
        flash(f"Erreur dans contenu_delete_wtf : {sys.exc_info()[0]} {sys.exc_info()[1]}", "danger")
    except (pymysql.err.OperationalError,
            pymysql.ProgrammingError,
            pymysql.InternalError,
            pymysql.err.IntegrityError,
            TypeError) as erreur_gest_genr_crud:
        code, msg = erreur_gest_genr_crud.args
        flash(f"attention : {error_codes.get(code, msg)} {erreur_gest_genr_crud} ", "danger")

        flash(f"Erreur dans contenu_delete_wtf : {sys.exc_info()[0]} "
              f"{erreur_gest_genr_crud.args[0]} , "
              f"{erreur_gest_genr_crud}", "danger")

        flash(f"__KeyError dans contenu_delete_wtf : {sys.exc_info()[0]} {sys.exc_info()[1]} {sys.exc_info()[2]}",
              "danger")

    return render_template("contenus/contenu_delete_wtf.html",
                           form_delete=form_delete,
                           btn_submit_del=btn_submit_del,
                           data_films_associes=data_armoirs_attribue_contenu_delete)



