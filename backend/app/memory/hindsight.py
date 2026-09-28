import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.db.database import get_db_connection

logger = logging.getLogger("rahat.hindsight")

# ─────────────────────────────────────────────────────────────────────────────
# MEMORY TYPES & CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

MEMORY_TYPE_PROFILE_FACT = "profile_fact"
MEMORY_TYPE_PREFERENCE = "preference"
MEMORY_TYPE_PLAN = "plan"
MEMORY_TYPE_OUTCOME = "outcome"
MEMORY_TYPE_PATTERN = "pattern"

VALID_MEMORY_TYPES = {
    MEMORY_TYPE_PROFILE_FACT,
    MEMORY_TYPE_PREFERENCE,
    MEMORY_TYPE_PLAN,
    MEMORY_TYPE_OUTCOME,
    MEMORY_TYPE_PATTERN,
}

# Type importance weightings for ranking
TYPE_IMPORTANCE_WEIGHTS = {
    MEMORY_TYPE_OUTCOME: 3.0,     # What actually happened carries highest weight
    MEMORY_TYPE_PATTERN: 2.5,     # Derived behavioral/earning patterns
    MEMORY_TYPE_PLAN: 2.0,        # What was planned
    MEMORY_TYPE_PREFERENCE: 1.5,  # Expressed user preferences
    MEMORY_TYPE_PROFILE_FACT: 1.0,# Stable factual context
}


class HindsightMemoryService:
    """
    Hindsight Long-Term Experiential Memory Service for Rahat.
    Maintains experiential knowledge:
    - PROFILE_FACT: Stable user characteristics (job, fixed obligations)
    - PREFERENCE: Explicit financial planning preferences
    - PLAN: Formulated financial pacing plans
    - OUTCOME: Real-world results and friction after a plan or action
    - PATTERN: Learned behavioral or earning rhythms
    
    STRICT BOUNDARIES:
    - Never stores raw financial transactions (handled by SQLite).
    - Enforces strict user isolation across all read, write, and search operations.
    - Prevents duplicate memory spam.
    - Maintains the Plan -> Outcome relationship.
    """

    def __init__(self):
        self._init_memory_table()

    def _init_memory_table(self):
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS hindsight_memories (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'emi',
            outcome_status TEXT DEFAULT 'observed',
            related_goal_id TEXT,
            related_plan_id TEXT,
            importance REAL DEFAULT 1.0,
            source TEXT DEFAULT 'system',
            relevance_tags TEXT,
            date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)

        # Safe schema migrations for existing tables
        cursor.execute("PRAGMA table_info(hindsight_memories)")
        cols = [r[1] for r in cursor.fetchall()]
        if "related_plan_id" not in cols:
            cursor.execute("ALTER TABLE hindsight_memories ADD COLUMN related_plan_id TEXT")
        if "importance" not in cols:
            cursor.execute("ALTER TABLE hindsight_memories ADD COLUMN importance REAL DEFAULT 1.0")
        if "source" not in cols:
            cursor.execute("ALTER TABLE hindsight_memories ADD COLUMN source TEXT DEFAULT 'system'")

        conn.commit()
        conn.close()

    def normalize_type(self, raw_type: str) -> str:
        t = raw_type.strip().lower()
        if t in VALID_MEMORY_TYPES:
            return t
        for valid in VALID_MEMORY_TYPES:
            if valid in t or t in valid:
                return valid
        return MEMORY_TYPE_OUTCOME

    # ─────────────────────────────────────────────────────────────────────────
    # WRITE MEMORY (with duplicate prevention & validation)
    # ─────────────────────────────────────────────────────────────────────────

    def store_memory(
        self,
        user_id: str,
        memory_type: str,
        title: str,
        content: str,
        category: str = "emi",
        outcome_status: str = "observed",
        related_goal_id: Optional[str] = None,
        related_plan_id: Optional[str] = None,
        importance: float = 1.0,
        source: str = "system",
        relevance_tags: Optional[List[str]] = None,
        date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Stores an experiential memory in Hindsight.
        Prevents duplicate entries for identical plans or repeated user submissions.
        """
        norm_type = self.normalize_type(memory_type)
        mem_date = date or datetime.now().strftime("%Y-%m-%d")
        tags = relevance_tags or []
        tags_json = json.dumps(tags)

        conn = get_db_connection()
        try:
            cursor = conn.cursor()

            # Duplicate check: check if an identical memory already exists for this user
            cursor.execute("""
            SELECT * FROM hindsight_memories
            WHERE user_id = ? AND type = ? AND title = ? AND content = ?
            """, (user_id, norm_type, title.strip(), content.strip()))
            existing = cursor.fetchone()

            if existing:
                tags_parsed = json.loads(existing["relevance_tags"]) if existing["relevance_tags"] else []
                res = dict(existing)
                res["relevance_tags"] = tags_parsed
                res["is_duplicate"] = True
                return res

            memory_id = f"mem_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(3).hex()}"

            cursor.execute("""
            INSERT INTO hindsight_memories (
                id, user_id, type, title, content, category, outcome_status,
                related_goal_id, related_plan_id, importance, source, relevance_tags, date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory_id,
                user_id,
                norm_type,
                title.strip(),
                content.strip(),
                category.strip().lower(),
                outcome_status.strip().lower(),
                related_goal_id,
                related_plan_id,
                importance,
                source,
                tags_json,
                mem_date,
            ))

            conn.commit()
        finally:
            conn.close()

        return {
            "id": memory_id,
            "user_id": user_id,
            "type": norm_type,
            "title": title.strip(),
            "content": content.strip(),
            "category": category.strip().lower(),
            "outcome_status": outcome_status.strip().lower(),
            "related_goal_id": related_goal_id,
            "related_plan_id": related_plan_id,
            "importance": importance,
            "source": source,
            "relevance_tags": tags,
            "date": mem_date,
            "is_duplicate": False,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # RETRIEVAL (Context-Aware, Ranked, Bounded to 3–5 items)
    # ─────────────────────────────────────────────────────────────────────────

    def search_memories(
        self,
        user_id: str,
        query: str = "",
        category: Optional[str] = None,
        limit: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top relevant memories for the specified user.
        - Strict user isolation: user_id = ?
        - Ranks by:
            1. Query / Keyword relevance (+1.5 per matched term)
            2. Type importance (outcomes +3.0, patterns +2.5, plans +2.0)
            3. Category matching (+2.0)
            4. Recency bonus
        - Excludes completely irrelevant memories when a specific query is provided.
        - Returns bounded 3–5 results.
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # Strict user isolation
        cursor.execute("""
        SELECT * FROM hindsight_memories
        WHERE user_id = ?
        ORDER BY date DESC
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return []

        query_terms = [q.lower().strip() for q in query.split() if len(q) > 2]
        cat_filter = category.lower().strip() if category else None

        scored_memories = []
        for r in rows:
            tags = json.loads(r["relevance_tags"]) if r["relevance_tags"] else []
            mem = {
                "id": r["id"],
                "user_id": r["user_id"],
                "type": r["type"],
                "title": r["title"],
                "content": r["content"],
                "category": r["category"],
                "outcome_status": r["outcome_status"],
                "related_goal_id": r["related_goal_id"],
                "related_plan_id": r["related_plan_id"],
                "importance": r["importance"] or 1.0,
                "source": r["source"] or "system",
                "relevance_tags": tags,
                "date": r["date"],
            }

            # 1. Base score from type importance & explicit importance
            base_type_weight = TYPE_IMPORTANCE_WEIGHTS.get(r["type"], 1.0)
            score = base_type_weight * float(r["importance"] or 1.0)

            # 2. Category match
            if cat_filter:
                if r["category"] == cat_filter or "general" in r["category"]:
                    score += 2.0
                else:
                    score -= 1.0  # discount unrelated categories

            # 3. Keyword / semantic relevance
            content_haystack = (
                f"{r['title']} {r['content']} {r['category']} {' '.join(tags)}"
            ).lower()

            matches = 0
            for term in query_terms:
                if term in content_haystack:
                    matches += 1
                    score += 2.0

            # If user provided search terms but memory has 0 matches, penalize
            if query_terms and matches == 0:
                score -= 3.0

            # 4. Recency bonus (more recent dates get slight bump)
            try:
                dt = datetime.strptime(r["date"], "%Y-%m-%d")
                days_ago = max(0, (datetime.now() - dt).days)
                recency_boost = max(0.0, 1.0 - (days_ago / 60.0))  # within last 60 days
                score += recency_boost
            except Exception:
                pass

            mem["_score"] = round(score, 2)
            scored_memories.append(mem)

        # Sort by score descending, then date descending
        scored_memories.sort(key=lambda x: (x["_score"], x["date"]), reverse=True)

        # Filter out deeply negative scores (completely irrelevant)
        relevant = [m for m in scored_memories if m["_score"] > 0]
        final_list = relevant if relevant else scored_memories

        return final_list[:max(1, min(limit, 5))]

    # ─────────────────────────────────────────────────────────────────────────
    # PLAN → OUTCOME RELATIONSHIP
    # ─────────────────────────────────────────────────────────────────────────

    def get_plan_outcomes(self, user_id: str, plan_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all outcome memories linked to a specific financial plan.
        Preserves the core Plan -> Outcome lifecycle.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM hindsight_memories
        WHERE user_id = ? AND related_plan_id = ? AND type = 'outcome'
        ORDER BY date DESC
        """, (user_id, plan_id))
        rows = cursor.fetchall()
        conn.close()

        outcomes = []
        for r in rows:
            tags = json.loads(r["relevance_tags"]) if r["relevance_tags"] else []
            d = dict(r)
            d["relevance_tags"] = tags
            outcomes.append(d)
        return outcomes

    # ─────────────────────────────────────────────────────────────────────────
    # TIMELINE & MANAGEMENT
    # ─────────────────────────────────────────────────────────────────────────

    def get_timeline(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Returns chronological timeline of meaningful events for the user.
        Strict user isolation. Raw financial transactions are never included.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM hindsight_memories
        WHERE user_id = ?
        ORDER BY date ASC, created_at ASC
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()

        timeline = []
        for r in rows:
            tags = json.loads(r["relevance_tags"]) if r["relevance_tags"] else []
            item = dict(r)
            item["relevance_tags"] = tags
            timeline.append(item)
        return timeline

    def get_memory_by_id(self, user_id: str, memory_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM hindsight_memories
        WHERE id = ? AND user_id = ?
        """, (memory_id, user_id))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        d = dict(row)
        d["relevance_tags"] = json.loads(d["relevance_tags"]) if d["relevance_tags"] else []
        return d

    def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """Deletes a memory ensuring user ownership."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        DELETE FROM hindsight_memories
        WHERE id = ? AND user_id = ?
        """, (memory_id, user_id))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    def clear_memories(self, user_id: str) -> bool:
        """Clears all memories for a specific user (isolated)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM hindsight_memories WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True

    # ─────────────────────────────────────────────────────────────────────────
    # DEMO SEED DATA (Explicitly marked as seed/demo)
    # ─────────────────────────────────────────────────────────────────────────

    def seed_demo_memories(self, user_id: str = "demo_user"):
        """
        Seeds deterministic hackathon demo memories illustrating the full learning loop:
        1. PROFILE_FACT: Fixed Hero Splendor EMI obligation
        2. PLAN: Flat ₹900/day plan (Sept 12)
        3. OUTCOME: Sept 16 shortfall (missed by ₹600 due to weekday volume) -> linked to plan!
        4. PATTERN: Weekend surge is 2x weekday platform earnings
        5. PREFERENCE: User preference for adaptive surge targets
        """
        self.clear_memories(user_id)

        demo_mems = [
            {
                "id": "mem_demo_1",
                "type": MEMORY_TYPE_PROFILE_FACT,
                "title": "Bike EMI Obligation",
                "content": "Hero Splendor bike loan EMI is ₹4,500 due on the 10th of each month.",
                "category": "emi",
                "outcome_status": "observed",
                "related_goal_id": "goal_current_emi",
                "related_plan_id": None,
                "importance": 2.0,
                "source": "demo_seed",
                "relevance_tags": ["emi", "loan", "bike", "fixed_obligation"],
                "date": "2026-09-09",
            },
            {
                "id": "mem_demo_2",
                "type": MEMORY_TYPE_PLAN,
                "title": "Previous EMI Plan (Sept 12)",
                "content": "Recommended flat target of ₹900/day across 5 weekdays to reach ₹4,500 before due date.",
                "category": "emi",
                "outcome_status": "failed",
                "related_goal_id": "goal_sept_emi",
                "related_plan_id": "plan_sept_12",
                "importance": 3.0,
                "source": "demo_seed",
                "relevance_tags": ["plan", "flat_rate", "weekday_plan", "emi"],
                "date": "2026-09-12",
            },
            {
                "id": "mem_demo_3",
                "type": MEMORY_TYPE_OUTCOME,
                "title": "Plan Outcome: ₹900/Day Target Missed",
                "content": "User could not maintain ₹900/day saving. Actual weekday savings averaged ₹500/day. Resulted in ₹3,900 saved (₹600 short) because weekday lunch shifts had low surge pricing.",
                "category": "emi",
                "outcome_status": "failed",
                "related_goal_id": "goal_sept_emi",
                "related_plan_id": "plan_sept_12",
                "importance": 4.5,
                "source": "demo_seed",
                "relevance_tags": ["outcome", "missed_target", "weekday_friction", "emi"],
                "date": "2026-09-16",
            },
            {
                "id": "mem_demo_4",
                "type": MEMORY_TYPE_PATTERN,
                "title": "Learned Earning Pattern",
                "content": "Weekend deliveries (Sat-Sun dinner & peak) generate ₹1,050–₹1,300/day with platform surge bonuses, whereas weekday earnings average ₹600–₹720/day.",
                "category": "income_pattern",
                "outcome_status": "learned",
                "related_goal_id": None,
                "related_plan_id": None,
                "importance": 4.0,
                "source": "demo_seed",
                "relevance_tags": ["pattern", "weekend_surge", "weekday_average", "earning_rhythm"],
                "date": "2026-09-17",
            },
            {
                "id": "mem_demo_5",
                "type": MEMORY_TYPE_PREFERENCE,
                "title": "Adaptive Strategy Preference",
                "content": "User succeeds better when high savings targets (₹800–₹1,000) are placed on weekends and lower targets (₹300–₹400) on weekdays.",
                "category": "emi",
                "outcome_status": "learned",
                "related_goal_id": None,
                "related_plan_id": None,
                "importance": 3.0,
                "source": "demo_seed",
                "relevance_tags": ["preference", "adaptive_targets", "surge_allocation"],
                "date": "2026-09-20",
            },
        ]

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            for m in demo_mems:
                mem_id = f"{m['id']}_{user_id}"
                cursor.execute("""
                INSERT OR REPLACE INTO hindsight_memories (
                    id, user_id, type, title, content, category, outcome_status,
                    related_goal_id, related_plan_id, importance, source, relevance_tags, date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    mem_id,
                    user_id,
                    m["type"],
                    m["title"],
                    m["content"],
                    m["category"],
                    m["outcome_status"],
                    m["related_goal_id"],
                    m["related_plan_id"],
                    m["importance"],
                    m["source"],
                    json.dumps(m["relevance_tags"]),
                    m["date"],
                ))
            conn.commit()
        finally:
            conn.close()


hindsight = HindsightMemoryService()
