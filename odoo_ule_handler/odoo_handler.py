import json
import logging
import ssl
import xmlrpc.client

logger = logging.getLogger(__name__)

# Company:  res.partner
# User:     res.users
# Product:  product.product
# Calendar: calendar.event
# Sales:    sales.order
# Location: stock.location
# Movement: stock.move
# Movement line: stock.move.line
# Warehouse: stock.warehouse
# Product Category: product.category
# Student: op.student
# Student Group: op.student.group
# Student Course (Enrollment): op.student.course
# Teacher: op.faculty
# Course: op.course
# Classroom: op.classroom


class OdooHandler(object):

    RFID_VAR = "kardex_remstar_xp_rfid"

    def __init__(self, url, self_signed_certificate=False):
        self.url = url
        self.self_signed_certificate = self_signed_certificate
        self.common = None
        self.db = None
        self.user = None
        self.password = None
        self.uid = None
        self.models = None

        if self.self_signed_certificate:
            context = ssl._create_unverified_context()
        else:
            context = None

        self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common', context=context)
        self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object', context=context)
        
    def connect(self, db=None, user=None, password=None):
        if not db or not user or not password:
            logger.error("You must provide a non empty db, user and password")
            raise AttributeError("Non empty db, user and password must be provided")
        
        self.db = db
        self.user = user
        self.password = password

        if not self.common:
            logger.error(f"Connection to the server ('{self.url}') could not be stablished")
            raise ConnectionError("Connection to the server could not be stablished")

        self.uid = self.common.authenticate(self.db, self.user, self.password, {})

        if not self.uid:
            logger.error(f"Connection to the database ('{self.url}') could not be stablisehd")
            raise ConnectionRefusedError("User could not be authenticated")


    ## User

    def get_all_users(self):
        fields = ["display_name", "name", "kardex_remstar_xp_rfid", "id_alumno_mysql", "user_cod_mysql", "group_id_mysql",
                  "propagate_mysql", "name_img_mysql", "identification_code", "zip", "zip_id", "city", "city_id", "email", ]
        result = self.models.execute_kw(self.db, self.uid, self.password, "res.users", "search_read", [[]], { "fields": fields} )
        logger.debug(f"{len(result)} users registered")
        return result

    def search_user_by_name(self, name=None, last_name=None):
        if not name:
            logger.error("You must provide at least a name")
            return
        
        query = [[["name", "=", name]]]
        if last_name:
            query[0].append(["last_name", "=", last_name])

        result = self.models.execute_kw(self.db, self.uid, self.password, "res.users", "search", query, {"limit": 20})
        return result

    def search_user_by_email(self, email=None):
        if not email:
            logger.error("You must provide an email address")
            return

        result = self.models.execute_kw(self.db, self.uid, self.password, "res.users", "search", [[["email", "=", email]]])
        if len(result) != 1:
            logger.error("More than one (o zero) user with the same email address")
            return
        return result

    def search_user_by_identification_code(self, identification_code=None):
        if not identification_code:
            logger.error("You must provide an identification code")
            return

        result = self.models.execute_kw(self.db, self.uid, self.password, "res.users", "search", [[["identification_code", "=", identification_code]]])
        if len(result) != 1:
            logger.error("More than one (o zero) users with the same identification code")
            return
        return result

    def read_user_details(self, user_id, params=None):
        if params:
            if not isinstance(params, list):
                logger.error("Params must be a list of values!")
                return

        if params:
            result = self.models.execute_kw(self.db, self.uid, self.password, "res.users", "read", [user_id], {"fields": params})
        else:
            result = self.models.execute_kw(self.db, self.uid, self.password, "res.users", "read", [user_id])
        return result

    def read_user_rfid_code(self, user_id):
        result = self.read_user_details(user_id, params=[self.RFID_VAR])
        if len(result) != 1:
            logger.error("More than one user with the same id")
            return
        details = result[0]
        if self.RFID_VAR in details:
            return details.get(self.RFID_VAR)
        else:
            logger.error("The user '{}' does not have the '{}' field".format(user_id, self.RFID_VAR))
            return

    def write_user_rfid(self, user_id, rfid_code):
        if not user_id or rfid_code is None:
            logger.error("You must provide an id and a rfid code")
            return
        try:
            result = self.models.execute_kw(self.db, self.uid, self.password, 'res.users', 'write', [user_id, { "kardex_remstar_xp_rfid": rfid_code}])
        except xmlrpc.client.Fault as e:
            logger.error("Error writting to the database: '{}'".format(e))
        except:
            logger.error("Unknown error: '{}'".format(e))
        else:
            return result


    ## Products

    def get_all_products(self):
        fields = ["name", "display_name", "list_price", "qty_available", "responsible_id", "categ_id"]
        result = self.models.execute_kw(self.db, self.uid, self.password, "product.product", "search_read", [[]], { "fields": fields})
        return result

    
    ## Product category

    def get_all_categories(self):
        fields = ["name", "complete_name", "display_name"]
        result = self.models.execute_kw(self.db, self.uid, self.password, "product.category", "search_read", [[]], { "fields": fields})
        return result


    # Locations

    def get_all_locations(self):
        fields = ["complete_name", "display_name", "create_date", "equipment_counter", "name", "product_counter", "stock_counter"]
        result = self.models.execute_kw(self.db, self.uid, self.password, "stock.location", "search_read", [[]], { "fields": fields} )
        return result


    # Movements

    def get_all_movements(self):
        fields = []
        result = self.models.execute_kw(self.db, self.uid, self.password, "stock.move", "search_read", [[]], { "fields": fields} )
        logger.debug(f"{len(result)} movements registered")
        return result

    def get_kardex_movements(self):
        fields = ["date", "reference", "location_id", "location_dest_id", "create_uid", "product_id", "product_qty"]
        search_filter = [[("reference", "=ilike", "B. P./INT/%"), ("state", "=", "done"), "|", ("location_id", "=", 248), ("location_dest_id", "=", 248)]]
        result = self.models.execute_kw(self.db, self.uid, self.password, "stock.move.line", "search_read", search_filter, { "fields": fields} )
        return result

    def get_tools_movements(self):
        fields = ["date", "reference", "location_id", "location_dest_id", "create_uid", "product_id", "qty_done", "product_code_mysql", "date_mysql", "lot_id"]
        search_filter = [[("reference", "=ilike", "B. P./INT/%"), ("state", "=", "done"), "|", ("location_id", "=", 409), ("location_dest_id", "=", 409)]]
        result = self.models.execute_kw(self.db, self.uid, self.password, "stock.move.line", "search_read", search_filter, { "fields": fields } )
        return result


    # Student

    def get_all_students(self):
        fields = ["display_name", "email", "zip", "street", "parent_name", "op_student_group_ids", "mobile", "identification_code", "id_number", 
                    "gender", "country_id", "course_detail_ids", "contact_address", "company_name", "state_id", "op_assignment_ids", "nationality", "name", 
                    "lang", "id_number", "gr_no", "city", "category_id", "birth_date", "barcode", "user_id"]
        result = self.models.execute_kw(self.db, self.uid, self.password, "op.student", "search_read", [[]], { "fields": fields} )
        logger.debug(f"{len(result)} students registered")
        return result

    def search_student_by_identification_code(self, identification_code=None):
        if not identification_code:
            logger.error("You must provide an identification code")
            return

        result = self.models.execute_kw(self.db, self.uid, self.password, "op.student", "search", [[["identification_code", "=", identification_code]]])
        if len(result) != 1:
            logger.error("More than one (o zero) student with the same identification_code")
            return
        return result[0]

    def search_student_by_gr_number(self, gr_number=None):
        if not gr_number:
            logger.error("You must provide an student number")
            return

        result = self.models.execute_kw(self.db, self.uid, self.password, "op.student", "search", [[["gr_no", "=", gr_number]]])
        if len(result) != 1:
            logger.error("More than one (o zero) student with the same student number")
            return
        return result[0]

    def search_student_by_email(self, email=None):
        if not email:
            logger.error("You must provide an email address")
            return

        result = self.models.execute_kw(self.db, self.uid, self.password, "op.student", "search", [[["email", "=", email]]])
        if len(result) != 1:
            logger.error("More than one (o zero) student with the same email address")
            return
        return result[0]

    def get_student_details(self, student_id):
        if not student_id:
            logger.error("You must provide a student id")
            return
        fields = ["display_name", "email", "zip", "street", "parent_name", "op_student_group_ids", "mobile", "identification_code", "id_number", 
                    "gender", "country_id", "course_detail_ids", "contact_address", "company_name", "state_id", "op_assignment_ids", "nationality", "name", 
                    "lang", "id_number", "gr_no", "city", "category_id", "birth_date", "barcode", "user_id"]
        result = self.models.execute_kw(self.db, self.uid, self.password, "op.student", "read", [student_id], { "fields": fields} )
        return result

    def get_student_user_id(self, student_id):
        if not student_id:
            logger.error("You must provide a student id")
            return
        result = self.models.execute_kw(self.db, self.uid, self.password, "op.student", "read", [student_id], { "fields": ["user_id"]})
        if len(result) != 1:
            logger.error("More than one (or zero) student with the same student id")
            return
        user_id = result[0].get("user_id")[0]
        return user_id


    # Teacher

    def get_all_teachers(self):
        fields = ["display_name", "email", "zip", "street", "parent_name", "mobile", "identification_code", "id_number", 
                    "gender", "country_id", "contact_address", "company_name", "state_id", "op_assignment_ids", "nationality",
                    "name",  "lang", "id_number", "city", "category_id", "birth_date", "barcode", "user_id"]
        result = self.models.execute_kw(self.db, self.uid, self.password, "op.faculty", "search_read", [[]], { "fields": fields} )
        logger.debug(f"{len(result)} teachers registered")
        return result

    def search_teacher_by_identification_code(self, identification_code=None):
        if not identification_code:
            logger.error("You must provide an identification code")
            return

        result = self.models.execute_kw(self.db, self.uid, self.password, "op.faculty", "search", [[["identification_code", "=", identification_code]]])
        if len(result) != 1:
            logger.error("More than one (o zero) teacher with the same identification_code")
            return
        return result[0]

    def search_teacher_by_email(self, email=None):
        if not email:
            logger.error("You must provide an email address")
            return

        result = self.models.execute_kw(self.db, self.uid, self.password, "op.faculty", "search", [[["email", "=", email]]])
        if len(result) != 1:
            logger.error("More than one (o zero) teacher with the same email address")
            return
        return result[0]

    def get_teacher_details(self, teacher_id):
        if not teacher_id:
            logger.error("You must provide a teacher id")
            return
        fields = ["display_name", "email", "zip", "street", "parent_name", "mobile", "identification_code", "id_number", 
                    "gender", "country_id", "contact_address", "company_name", "state_id", "op_assignment_ids", "nationality",
                    "name",  "lang", "id_number", "city", "category_id", "birth_date", "barcode", "user_id"]
        result = self.models.execute_kw(self.db, self.uid, self.password, "op.faculty", "read", [teacher_id], { "fields": fields} )
        return result

    def get_teacher_user_id(self, teacher_id):
        if not teacher_id:
            logger.error("You must provide a teacher id")
            return
        result = self.models.execute_kw(self.db, self.uid, self.password, "op.faculty", "read", [teacher_id], { "fields": ["user_id"]})
        if len(result) != 1:
            logger.error("More than one (or zero) teacher with the same teacher id")
            return
        user_id = result[0].get("user_id")[0]
        return user_id

    
    # Course

    def get_all_courses(self):
        fields = ["display_name", "name", "code", "subject_ids", "op_student_course_ids", "op_batch_ids"]
        result = self.models.execute_kw(self.db, self.uid, self.password, "op.course", "search_read", [[]], { "fields": fields} )
        logger.debug(f"{len(result)} courses registered")
        return result


    # Student course - Enrollment

    def get_all_enrollments(self):
        fields = ["batch_id", "course_id", "display_name", "student_id", "subject_ids"]
        result = self.models.execute_kw(self.db, self.uid, self.password, "op.student.course", "search_read", [[]], { "fields": fields} )
        logger.debug(f"{len(result)} student enrollments")
        return result


    # Models

    def print_models(self):
        fields = ["name", "model"]
        results = self.models.execute_kw(self.db, self.uid, self.password, "ir.model", "search", [[]] )
        result = self.models.execute_kw(self.db, self.uid, self.password, "ir.model", "read", [results], { "fields": fields})
        logger.info(json.dumps(result, sort_keys=True, indent=4))


    # Help

    def print_model_fields(self, model_name):
        attributes = ['string', 'help', 'type']
        fields = self.models.execute_kw(self.db, self.uid, self.password, model_name, 'fields_get', [], {'attributes': attributes})
        logger.info(json.dumps(fields, sort_keys=True, indent=4))