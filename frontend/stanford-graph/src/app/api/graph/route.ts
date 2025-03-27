import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const NUM_COURSES_TO_DISPLAY = 5000;

// Initialize Supabase client using env vars
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

// Helper function to select rows in batches of 1000
async function batchSelect(table: string, columns: string, batchSize = 1000) {
  let allRows: any[] = [];
  let start = 0;

  while (start <= NUM_COURSES_TO_DISPLAY) {
    const { data, error } = await supabase
      .from(table)
      .select(columns)
      .range(start, start + batchSize - 1);

    if (error) throw error;
    if (!data || data.length === 0) break;

    allRows = allRows.concat(data);
    if (data.length < batchSize) break;

    start += batchSize;
  }

  return allRows;
}

export async function GET() {
  try {
    // Batch-fetch all course nodes
    const courses = await batchSelect('courses', 'id, number');

    // Batch-fetch all prereq edges
    const prereqs = await batchSelect('prereqs', 'course_id, prereq_id');

    // Map course IDs to course numbers
    const idToCode: Record<number, string> = {};
    const nodes = courses.map((course) => {
      idToCode[course.id] = course.number;
      return {
        id: course.number,
        label: course.number,
      };
    });

    // Build graph edges from prereq relationships
    const edges = prereqs
      .filter(row => idToCode[row.course_id] && idToCode[row.prereq_id])
      .map(row => ({
        source: idToCode[row.prereq_id],
        target: idToCode[row.course_id],
      }));

    return NextResponse.json({ nodes, edges });
  } catch (error) {
    console.error('❌ Failed to fetch graph data:', error);
    return NextResponse.json(
      { error: 'Something went wrong while fetching data.' },
      { status: 500 }
    );
  }
}
