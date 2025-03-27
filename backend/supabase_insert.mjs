import { createClient } from '@supabase/supabase-js';
import fs from 'fs/promises';

const supabaseUrl = 'https://phhesofzsdjlmnsrdiay.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBoaGVzb2Z6c2RqbG1uc3JkaWF5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI5Mzg2MTksImV4cCI6MjA1ODUxNDYxOX0.phPvvJ2LTwMo7e_pEbamZe-rOgquU20SSri7RssH5Lo';
const supabase = createClient(supabaseUrl, supabaseKey);

const dataFile = "data\\execute\\all_courses.json";

// {
//     "courseNumber": "ATHLETIC 10",
//     "courseName": "Varsity Sport Experience",
//     "courseDescription": "Designed for the Varsity Athlete; conditioning; practice; game preparation; and weight training. Limit 2 credits per quarter with a maximum of 8 activity units may be applied towards graduation. Prerequisite: Must be a Varsity Athlete in the specific sport; Permission of appropriate sport administrator.",
//     "prerequisites": []
// },

// insert into table `courses`
async function insertCourses() {
    const fileData = await fs.readFile(dataFile, "utf-8");
    const courses = JSON.parse(fileData);
    for (const course of courses) {
        let courseObj = {
            "number": course.courseNumber,
            "name": course.courseName,
            "description": course.courseDescription,
            "prerequisites": course.prerequisites
        };
        const { data, error } = await supabase
            .from('courses')
            .insert([courseObj]);
        if (error) {
            console.log(`🤔 Error inserting ${courseObj.number}:`, error.message);
        } else {
            continue;
        }
    }
    console.log(`✅✅✅ Inserted all courses to supabase: ${courses.length}`);
}

insertCourses()


