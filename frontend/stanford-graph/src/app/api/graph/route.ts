import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client using environment variables
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export async function GET() {
  try {
    // Fetch courses and prereqs from Supabase
    const { data: courses, error: courseError } = await supabase
      .from('courses')
      .select('id, code');

    const { data: prereqs, error: prereqError } = await supabase
      .from('prereqs')
      .select('course_id, prereq_id');

    if (courseError || prereqError) {
      throw new Error(courseError?.message || prereqError?.message);
    }

    // Build mapping from id to course code
    const idToCode: Record<number, string> = {};
    const nodes = courses.map((course) => {
      idToCode[course.id] = course.code;
      return {
        id: course.code,
        label: course.code,
      };
    });

    // Convert course_id and prereq_id into edges using course codes
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
