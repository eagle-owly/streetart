from flaskext.mysql import MySQL


class Database:
    db = None

    def __init__(self, app):
        self.db = MySQL(app)

    def query(self, sql, params=None):
        cur = self.db.get_db().cursor()
        cur.execute(sql, params)

        columns = [c[0] for c in cur.description]
        return [dict(zip(columns, r)) for r in cur.fetchall()]

    def get_row(self, sql, params=None):
        return self.query(sql, params)[0]

    def execute(self, sql, params):
        cur = self.db.get_db().cursor()
        cur.execute(sql, params)
        self.db.get_db().commit()

    def is_place_existing(self, place_id):
        return self.get_row("SELECT COUNT(*) AS c FROM place p WHERE p.id = %(place_id)s",
                            {'place_id': place_id})['c'] == 1

    def get_content_options(self, place_id):
        return self.query("""
        SELECT
            c.id,
            c.template,
            c.probability
        FROM place_content c
        WHERE c.place_id = %(place_id)s
        AND c.deactivated IS NULL
        """, {'place_id': place_id})

    def log_event(self, session_id, place_id, content_id, ip_address, user_agent, event, details=None):
        self.execute("""
        INSERT INTO place_session (id, place_id, content_id, ip_address, user_agent, event, details) 
        VALUES (%(session_id)s, %(place_id)s, %(content_id)s, %(ip_address)s, %(user_agent)s, %(event)s, %(details)s)
        """, {'session_id': session_id, 'place_id': place_id, 'content_id': content_id, 'ip_address': ip_address,
              'user_agent': user_agent, 'event': event, 'details': details})

    def update_seconds(self, session_id):
        self.execute("""
        UPDATE place_session s
        SET s.seconds = s.seconds + 1
        WHERE s.id = %(session_id)s
        ORDER BY s.created DESC
        LIMIT 1
        """, {'session_id': session_id})

    def get_activity_logs(self, page):
        offset = 20 * page

        return self.query("""
        SELECT
            s.id, s.created, s.place_id, s.ip_address, s.user_agent, s.event, s.details, s.seconds,
            c.name AS test_name, c.template AS content,
            p.name AS place
        FROM place_session s
        JOIN (
            SELECT
                DISTINCT id
            FROM place_session s2
            ORDER BY id DESC
            LIMIT 20
            OFFSET %(offset)s
        ) s2 ON s.id = s2.id 
        JOIN place_content c ON c.place_id = s.place_id AND c.id = s.content_id AND c.deactivated IS NULL
        JOIN place p ON p.id = s.place_id
        ORDER BY s.id DESC, s.created ASC
        """, {'offset': offset})

    def delete_session(self, session_id):
        self.execute("DELETE FROM place_session WHERE id = %(session_id)s", {'session_id': session_id})

    def get_stats(self):
        return self.query("""
        SELECT
            p.name AS place, 
            c.name AS choice, c.template AS content, c.probability, c.created, c.deactivated,
            COUNT(DISTINCT s.id) AS sessions,
            SUM(s.seconds) AS seconds,
            SUM(CASE WHEN s.event = 'VIDEO_LOADED' THEN 1 END) AS video_loaded,
            SUM(CASE WHEN s.event = 'VIDEO_REJECTED' THEN 1 END) AS video_rejected,
            SUM(CASE WHEN s.event = 'INSTAGRAM_CLICK' THEN 1 END) AS instagram_click,
            COUNT(DISTINCT CASE WHEN s.event = 'VIDEO_LOADED' THEN s.id END) AS sessions_video_loaded,
            COUNT(DISTINCT CASE WHEN s.event = 'VIDEO_REJECTED' THEN s.id END) AS sessions_video_rejected,
            COUNT(DISTINCT CASE WHEN s.event = 'INSTAGRAM_CLICK' THEN s.id END) AS sessions_instagram_click,
            AVG(CASE WHEN s.event = 'VIDEO_LOADED' THEN s.seconds END) AS video_loaded_seconds
        FROM place p
        JOIN place_content c ON c.place_id = p.id
        JOIN place_session s ON s.place_id = p.id AND s.content_id = c.id
        GROUP BY 1,2,3,4,5,6
        """)
