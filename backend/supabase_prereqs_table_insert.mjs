import { createClient } from '@supabase/supabase-js';
import fs from 'fs/promises';
import cliProgress from 'cli-progress';

const supabaseUrl = 'https://phhesofzsdjlmnsrdiay.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBoaGVzb2Z6c2RqbG1uc3JkaWF5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI5Mzg2MTksImV4cCI6MjA1ODUxNDYxOX0.phPvvJ2LTwMo7e_pEbamZe-rOgquU20SSri7RssH5Lo';
const supabase = createClient(supabaseUrl, supabaseKey);

const dataFile = "data\\execute\\all_courses.json";

const progressBar = new cliProgress.Bar({}, cliProgress.Presets.shades_classic);

async function insertPrereqs() {
    const fileData = await fs.readFile(dataFile, "utf-8");
    const coursesFromJSON = JSON.parse(fileData);

    const batchSize = 1000;
    let allCourses = [];
    let start = 0;
    let keepGoing = true;

    while (keepGoing) {
    const { data, error } = await supabase
        .from('courses')
        .select('id, number')
        .range(start, start + batchSize - 1);

    if (error) {
        console.error(`❌ Error fetching courses:`, error.message);
        break;
    }

    if (data.length === 0) {
        keepGoing = false;
        break;
    }

    allCourses = allCourses.concat(data);

    // If returned less than a full batch, you're done
    if (data.length < batchSize) {
        keepGoing = false;
    }

    start += batchSize;
    }

    console.log(`✅ Fetched ${allCourses.length} courses from Supabase`);

    
    const courseMap = new Map(allCourses.map(course => [course.number, course.id]));
    const result_pairs = [];
    const seenPairs = new Set();

    progressBar.start(coursesFromJSON.length, 0);
    let count = 0;

    for (const course of coursesFromJSON) {
        const courseID = courseMap.get(course.courseNumber);
        if (!courseID) {
            console.warn(`⚠️ Missing course in DB: ${course.courseNumber}`);
            count++;
            progressBar.update(count);
            continue;
        }

        for (const pre of course.prerequisites) {
            const prereqID = courseMap.get(pre);
            if (!prereqID) {
                console.warn(`⚠️ Missing prereq in DB: ${pre}`);
                continue;
            }

            if (courseID === prereqID) continue;

            const pairKey = `${courseID}-${prereqID}`;
            if (seenPairs.has(pairKey)) continue;

            seenPairs.add(pairKey);
            result_pairs.push({ course_id: courseID, prereq_id: prereqID });
        }

        count++;
        progressBar.update(count);
    }

    progressBar.stop();
    console.log(`🧠 Prepared ${result_pairs.length} prerequisite pairs.`);

    // Chunked insert
    const chunkSize = 500;
    let countInsert = 0;
    progressBar.start(result_pairs.length, 0);

    for (let i = 0; i < result_pairs.length; i += chunkSize) {
        const chunk = result_pairs.slice(i, i + chunkSize);
        const { error: insertError } = await supabase
            .from('prereqs')
            .insert(chunk);

        if (insertError) {
            console.log(`❌ [CHUNK ${i}] Insert error:`, insertError.message);
            console.log(insertError.details || insertError.hint || insertError.code);
            continue;
        }

        countInsert += chunk.length;
        progressBar.update(countInsert);
    }

    progressBar.stop();
    console.log(`✅ Inserted ${countInsert} / ${result_pairs.length} prerequisite pairs into Supabase.`);
}

insertPrereqs();
