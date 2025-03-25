import { NextResponse } from 'next/server';
import { Pool } from 'pg';
import { config } from 'dotenv';
config(); 

console.log({
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    host: process.env.DB_HOST,
    database: process.env.DB_NAME,
    port: process.env.DB_PORT,
  });

const pool = new Pool({
  user: process.env.DB_USER,
  host: process.env.DB_HOST,
  database: process.env.DB_NAME,
  password: process.env.DB_PASSWORD,
  port: Number(process.env.DB_PORT),
});

export async function GET() {
  try {
    const client = await pool.connect();

    const coursesRes = await client.query('SELECT id, code FROM courses');
    const prereqsRes = await client.query('SELECT course_id, prereq_id FROM prereqs');

    const idToCode: Record<number, string> = {};
    const nodes = coursesRes.rows.map(row => {
      idToCode[row.id] = row.code;
      return {
        id: row.code,
        label: row.code,
      };
    });

    const edges = prereqsRes.rows.map(row => ({
      source: idToCode[row.prereq_id],
      target: idToCode[row.course_id],
    }));

    client.release();

    return NextResponse.json({ nodes, edges });
  } catch (error) {
    console.error('Failed to fetch graph data:', error);
    return NextResponse.json({ error: 'Something went wrong' }, { status: 500 });
  }
}
