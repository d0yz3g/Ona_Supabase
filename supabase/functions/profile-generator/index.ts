// Follow this setup guide to integrate the Deno language server with your editor:
// https://deno.land/manual/getting_started/setup_your_environment
// This enables autocomplete, go to definition, etc.

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { Configuration, OpenAIApi } from "https://esm.sh/openai@3.2.1"

// Initialize OpenAI API
const configuration = new Configuration({
  apiKey: Deno.env.get('OPENAI_API_KEY'),
})
const openai = new OpenAIApi(configuration)

// Initialize Supabase client
const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? ''
const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
const supabase = createClient(supabaseUrl, supabaseServiceKey)

interface ProfileRequest {
  userId: number
}

interface ProfileGenerationRequest {
  userId: number
  answers: Array<{
    questionId: string
    answer: string
  }>
}

serve(async (req: Request) => {
  try {
    // CORS headers
    if (req.method === 'OPTIONS') {
      return new Response('ok', {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        }
      })
    }

    // Parse request body
    const { userId, answers } = await req.json() as ProfileGenerationRequest

    if (!userId) {
      return new Response(
        JSON.stringify({ error: 'User ID is required' }),
        { 
          status: 400,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          }
        }
      )
    }

    // If no answers provided, retrieve from database
    let userAnswers = answers
    if (!userAnswers || userAnswers.length === 0) {
      const { data: surveyResponses, error } = await supabase
        .from('survey_responses')
        .select('question_id, answer')
        .eq('user_id', userId)

      if (error) {
        return new Response(
          JSON.stringify({ error: 'Failed to retrieve survey responses', details: error }),
          { 
            status: 500,
            headers: {
              'Content-Type': 'application/json',
              'Access-Control-Allow-Origin': '*'
            }
          }
        )
      }

      if (!surveyResponses || surveyResponses.length === 0) {
        return new Response(
          JSON.stringify({ error: 'No survey responses found for this user' }),
          { 
            status: 404,
            headers: {
              'Content-Type': 'application/json',
              'Access-Control-Allow-Origin': '*'
            }
          }
        )
      }

      userAnswers = surveyResponses.map(response => ({
        questionId: response.question_id,
        answer: response.answer
      }))
    }

    // Prepare the prompt for OpenAI
    const prompt = `Generate a comprehensive psychological profile based on the following survey responses:

${userAnswers.map(answer => `Question ${answer.questionId}: ${answer.answer}`).join('\n')}

Generate a detailed psychological profile with the following structure:
1. Primary personality type (one of: Intellectual, Emotional, Practical, Creative)
2. Key personality traits (at least 5 traits)
3. Strengths (at least 3)
4. Challenges (at least 3)
5. Communication style
6. Decision-making process
7. Stress response
8. Personal growth recommendations (at least 3)

Format the response as a JSON object with the following structure:
{
  "profileType": "Intellectual|Emotional|Practical|Creative",
  "personalityTraits": ["trait1", "trait2", ...],
  "strengths": ["strength1", "strength2", ...],
  "challenges": ["challenge1", "challenge2", ...],
  "communicationStyle": "description...",
  "decisionMaking": "description...",
  "stressResponse": "description...",
  "growthRecommendations": ["recommendation1", "recommendation2", ...]
}
`

    // Call OpenAI API to generate the profile
    const completion = await openai.createChatCompletion({
      model: "gpt-4",
      messages: [
        { role: "system", content: "You are a professional psychologist with expertise in personality profiling." },
        { role: "user", content: prompt }
      ],
      temperature: 0.7,
      max_tokens: 1500
    })

    const profileContent = completion.data.choices[0].message?.content || '{}'
    let profileData = {}
    
    try {
      profileData = JSON.parse(profileContent)
    } catch (e) {
      console.error("Failed to parse OpenAI response as JSON:", e)
      return new Response(
        JSON.stringify({ error: 'Failed to parse profile data' }),
        { 
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          }
        }
      )
    }

    // Save the profile to the database
    const { error: profileError } = await supabase
      .from('profiles')
      .upsert({
        user_id: userId,
        profile_type: profileData.profileType,
        profile_data: profileData,
        personality_traits: { traits: profileData.personalityTraits },
        updated_at: new Date().toISOString()
      })

    if (profileError) {
      return new Response(
        JSON.stringify({ error: 'Failed to save profile', details: profileError }),
        { 
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          }
        }
      )
    }

    // Update user stats
    const { error: statsError } = await supabase
      .from('user_stats')
      .upsert({
        user_id: userId,
        survey_completed: true,
        updated_at: new Date().toISOString()
      })

    if (statsError) {
      console.error("Failed to update user stats:", statsError)
      // Continue anyway since the profile was generated successfully
    }

    return new Response(
      JSON.stringify({ 
        success: true,
        profile: profileData
      }),
      { 
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      }
    )
  } catch (error) {
    console.error("Unexpected error:", error)
    
    return new Response(
      JSON.stringify({ error: 'Internal server error', details: error.message }),
      { 
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      }
    )
  }
}) 