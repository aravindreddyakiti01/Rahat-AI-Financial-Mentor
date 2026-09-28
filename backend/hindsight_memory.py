import json
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from database import DB_PATH, get_db_connection

class HindsightMemoryService:
    """
    Hindsight Long-Term Experiential Memory Engine.
    Implements Outcome-Aware Financial Memory:
    - Profile Facts
    - Plans
    - Real-World Outcomes (what actually happened)
    - Learned Patterns
    - User Preferences

    Provides grounded semantic context to LangGraph agent and
    enables the human-visible 'What Rahat Remembers' timeline.
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
            type TEXT NOT NULL, -- 'profile_fact', 'plan', 'outcome', 'pattern', 'preference'
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'emi', -- 'emi', 'income_pattern', 'expense', 'savings'
            outcome_status TEXT DEFAULT 'observed', -- 'succeeded', 'failed', 'learned', 'active'
            related_goal_id TEXT,
            relevance_tags TEXT, -- JSON array of tags
            date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        conn.commit()
        conn.close()

    def store_memory(
        self,
        user_id: str,
        memory_type: str,
        title: str,
        content: str,
        category: str = "emi",
        outcome_status: str = "observed",
        related_goal_id: Optional[str] = None,
        relevance_tags: Optional[List[str]] = None,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()
        memory_id = f"mem_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(3).hex()}"
        tags_json = json.dumps(relevance_tags or [])
        mem_date = date or datetime.now().strftime("%Y-%m-%d")

        cursor.execute("""
        INSERT INTO hindsight_memories 
        (id, user_id, type, title, content, category, outcome_status, related_goal_id, relevance_tags, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (memory_id, user_id, memory_type, title, content, category, outcome_status, related_goal_id, tags_json, mem_date))

        conn.commit()
        conn.close()

        return {
            "id": memory_id,
            "user_id": user_id,
            "type": memory_type,
            "title": title,
            "content": content,
            "category": category,
            "outcome_status": outcome_status,
            "related_goal_id": related_goal_id,
            "relevance_tags": relevance_tags or [],
            "date": mem_date
        }

    def search_memories(
        self,
        user_id: str,
        query: str = "",
        category: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieves relevant experiential memories for the agent.
        Prioritizes real-world outcomes and learned patterns matching the goal/context.
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        query_terms = [q.lower().strip() for q in query.split() if len(q) > 2]

        if category:
            cursor.execute("""
            SELECT * FROM hindsight_memories 
            WHERE user_id = ? AND (category = ? OR category = 'general')
            ORDER BY date DESC
            """, (user_id, category))
        else:
            cursor.execute("""
            SELECT * FROM hindsight_memories 
            WHERE user_id = ? 
            ORDER BY date DESC
            """, (user_id,))

        rows = cursor.fetchall()
        conn.close()

        memories = []
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
                "relevance_tags": tags,
                "date": r["date"]
            }

            # Calculate relevance score
            score = 1.0
            # Higher weight for outcomes and patterns (core differentiator)
            if r["type"] == "outcome":
                score += 2.0
            elif r["type"] == "pattern":
                score += 1.5
            elif r["type"] == "plan":
                score += 1.0

            # Match keywords
            content_lower = (r["title"] + " " + r["content"] + " " + " ".join(tags)).lower()
            for term in query_terms:
                if term in content_lower:
                    score += 1.0

            mem["_score"] = score
            memories.append(mem)

        # Sort by relevance score descending, then date
        memories.sort(key=lambda x: (x["_score"], x["date"]), reverse=True)
        return memories[:limit]

    def get_timeline(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Returns chronological timeline for the 'What Rahat Remembers' UI screen.
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
            timeline.append({
                "id": r["id"],
                "user_id": r["user_id"],
                "type": r["type"],
                "title": r["title"],
                "content": r["content"],
                "category": r["category"],
                "outcome_status": r["outcome_status"],
                "related_goal_id": r["related_goal_id"],
                "relevance_tags": tags,
                "date": r["date"]
            })
        return timeline

    def delete_memory(self, user_id: str, memory_id: str) -> bool:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM hindsight_memories WHERE id = ? AND user_id = ?", (memory_id, user_id))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    def clear_memories(self, user_id: str) -> bool:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM hindsight_memories WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True

    def seed_demo_memories(self, user_id: str = "demo_user"):
        """
        Deterministic experiential memory history for Hackathon Demo:
        - Sept 09: Profile fact (Hero Splendor EMI ₹4,500 due 10th of every month)
        - Sept 12: Previous Plan (Save ₹900/day over 5 weekdays to hit ₹4,500 target)
        - Sept 16: Outcome (Target missed by ₹600. Saved ₹3,900 (~₹500/day weekday pace) because weekday order volume dipped)
        - Sept 17: Learned Pattern (Weekend earnings average ₹1,150/day with incentives, while weekdays average ₹600/day)
        - Sept 20: Grounded Strategy preference (Allocate 65% of weekend surge income to EMI rather than flat daily deduction)
        """
        self.clear_memories(user_id)

        demo_mems = [
            {
                "id": "mem_demo_1",
                "type": "profile_fact",
                "title": "Bike EMI Obligation",
                "content": "Hero Splendor bike loan EMI is ₹4,500 due on the 10th of each month.",
                "category": "emi",
                "outcome_status": "observed",
                "relevance_tags": ["emi", "loan", "bike", "fixed_obligation"],
                "date": "2026-09-09"
            },
            {
                "id": "mem_demo_2",
                "type": "plan",
                "title": "Previous EMI Plan (Sept 12)",
                "content": "Recommended flat target of ₹900/day across 5 weekdays to reach ₹4,500 before due date.",
                "category": "emi",
                "outcome_status": "failed",
                "related_goal_id": "goal_sept_emi",
                "relevance_tags": ["plan", "flat_rate", "weekday_plan", "emi"],
                "date": "2026-09-12"
            },
            {
                "id": "mem_demo_3",
                "type": "outcome",
                "title": "Plan Outcome: ₹900/Day Target Missed",
                "content": "User could not maintain ₹900/day saving. Actual weekday savings averaged ₹500/day. Resulted in ₹3,900 saved (₹600 short) because weekday lunch shifts had low surge pricing.",
                "category": "emi",
                "outcome_status": "failed",
                "related_goal_id": "goal_sept_emi",
                "relevance_tags": ["outcome", "missed_target", "weekday_friction", "emi"],
                "date": "2026-09-16"
            },
            {
                "id": "mem_demo_4",
                "type": "pattern",
                "title": "Learned Earning Pattern",
                "content": "Weekend deliveries (Sat-Sun dinner & peak) generate ₹1,050–₹1,300/day with platform surge bonuses, whereas weekday earnings average ₹600–₹720/day.",
                "category": "income_pattern",
                "outcome_status": "learned",
                "relevance_tags": ["pattern", "weekend_surge", "weekday_average", "earning_rhythm"],
                "date": "2026-09-17"
            },
            {
                "id": "mem_demo_5",
                "type": "preference",
                "title": "Adaptive Strategy Preference",
                "content": "User succeeds better when high savings targets (₹800–₹1,000) are placed on weekends and lower targets (₹300–₹400) on weekdays.",
                "category": "emi",
                "outcome_status": "learned",
                "relevance_tags": ["preference", "adaptive_targets", "surge_allocation"],
                "date": "2026-09-20"
            }
        ]

        conn = get_db_connection()
        cursor = conn.cursor()
        for m in demo_mems:
            cursor.execute("""
            INSERT INTO hindsight_memories 
            (id, user_id, type, title, content, category, outcome_status, related_goal_id, relevance_tags, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (m["id"], user_id, m["type"], m["title"], m["content"], m["category"], m["outcome_status"], m.get("related_goal_id"), json.dumps(m["relevance_tags"]), m["date"]))
        conn.commit()
        conn.close()

hindsight = HindsightMemoryService()
