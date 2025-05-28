// Follow this setup guide to integrate the Deno language server with your editor:
// https://deno.land/manual/getting_started/setup_your_environment
// This enables autocomplete, go to definition, etc.

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { format } from "https://deno.land/std@0.168.0/datetime/mod.ts"

// Initialize Supabase client
const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? ''
const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
const supabase = createClient(supabaseUrl, supabaseServiceKey)

interface ReminderRequest {
  userId?: number
  reminderId?: string
  action: 'get' | 'create' | 'update' | 'delete' | 'check'
  reminderData?: {
    reminderType: string
    reminderTime: string
    reminderDays: string[]
  }
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
    const { userId, reminderId, action, reminderData } = await req.json() as ReminderRequest

    if (!action) {
      return new Response(
        JSON.stringify({ error: 'Action is required' }),
        { 
          status: 400,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          }
        }
      )
    }

    // Get all reminders for a user
    if (action === 'get') {
      if (!userId) {
        return new Response(
          JSON.stringify({ error: 'User ID is required for getting reminders' }),
          { 
            status: 400,
            headers: {
              'Content-Type': 'application/json',
              'Access-Control-Allow-Origin': '*'
            }
          }
        )
      }

      const { data: reminders, error } = await supabase
        .from('reminders')
        .select('*')
        .eq('user_id', userId)
        .order('created_at', { ascending: false })

      if (error) {
        return new Response(
          JSON.stringify({ error: 'Failed to retrieve reminders', details: error }),
          { 
            status: 500,
            headers: {
              'Content-Type': 'application/json',
              'Access-Control-Allow-Origin': '*'
            }
          }
        )
      }

      return new Response(
        JSON.stringify({ 
          success: true,
          reminders: reminders || []
        }),
        { 
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          }
        }
      )
    }

    // Create a new reminder
    if (action === 'create') {
      if (!userId || !reminderData) {
        return new Response(
          JSON.stringify({ error: 'User ID and reminder data are required for creating a reminder' }),
          { 
            status: 400,
            headers: {
              'Content-Type': 'application/json',
              'Access-Control-Allow-Origin': '*'
            }
          }
        )
      }

      const { reminderType, reminderTime, reminderDays } = reminderData

      if (!reminderType || !reminderTime || !reminderDays || reminderDays.length === 0) {
        return new Response(
          JSON.stringify({ 
            error: 'Reminder type, time, and at least one day are required' 
          }),
          { 
            status: 400,
            headers: {
              'Content-Type': 'application/json',
              'Access-Control-Allow-Origin': '*'
            }
          }
        )
      }

      const { data: reminder, error } = await supabase
        .from('reminders')
        .insert({
          user_id: userId,
          reminder_type: reminderType,
          reminder_time: reminderTime,
          reminder_days: reminderDays,
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        })
        .select()
        .single()

      if (error) {
        return new Response(
          JSON.stringify({ error: 'Failed to create reminder', details: error }),
          { 
            status: 500,
            headers: {
              'Content-Type': 'application/json',
              'Access-Control-Allow-Origin': '*'
            }
          }
        )
      }

      return new Response(
        JSON.stringify({ 
          success: true,
          reminder
        }),
        { 
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          }
        }
      )
    }

    // Update an existing reminder
    if (action === 'update') {
      if (!reminderId || !reminderData) {
        return new Response(
          JSON.stringify({ error: 'Reminder ID and reminder data are required for updating a reminder' }),
          { 
            status: 400,
            headers: {
              'Content-Type': 'application/json',
              'Access-Control-Allow-Origin': '*'
            }
          }
        )
      }

      const updateData: Record<string, unknown> = {}
      
      if (reminderData.reminderType) {
        updateData.reminder_type = reminderData.reminderType
      }
      
      if (reminderData.reminderTime) {
        updateData.reminder_time = reminderData.reminderTime
      }
      
      if (reminderData.reminderDays && reminderData.reminderDays.length > 0) {
        updateData.reminder_days = reminderData.reminderDays
      }
      
      updateData.updated_at = new Date().toISOString()

      const { data: reminder, error } = await supabase
        .from('reminders')
        .update(updateData)
        .eq('id', reminderId)
        .select()
        .single()

      if (error) {
        return new Response(
          JSON.stringify({ error: 'Failed to update reminder', details: error }),
          { 
            status: 500,
            headers: {
              'Content-Type': 'application/json',
              'Access-Control-Allow-Origin': '*'
            }
          }
        )
      }

      return new Response(
        JSON.stringify({ 
          success: true,
          reminder
        }),
        { 
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          }
        }
      )
    }

    // Delete a reminder
    if (action === 'delete') {
      if (!reminderId) {
        return new Response(
          JSON.stringify({ error: 'Reminder ID is required for deleting a reminder' }),
          { 
            status: 400,
            headers: {
              'Content-Type': 'application/json',
              'Access-Control-Allow-Origin': '*'
            }
          }
        )
      }

      const { error } = await supabase
        .from('reminders')
        .delete()
        .eq('id', reminderId)

      if (error) {
        return new Response(
          JSON.stringify({ error: 'Failed to delete reminder', details: error }),
          { 
            status: 500,
            headers: {
              'Content-Type': 'application/json',
              'Access-Control-Allow-Origin': '*'
            }
          }
        )
      }

      return new Response(
        JSON.stringify({ 
          success: true,
          message: 'Reminder deleted successfully'
        }),
        { 
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          }
        }
      )
    }

    // Check for due reminders
    if (action === 'check') {
      const now = new Date()
      const currentDay = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][now.getDay()]
      const currentTime = format(now, 'HH:mm')

      const { data: dueReminders, error } = await supabase
        .from('reminders')
        .select('*')
        .eq('is_active', true)
        .filter('reminder_days', 'cs', `{"${currentDay}"}`)
        .filter('reminder_time', 'eq', currentTime)

      if (error) {
        return new Response(
          JSON.stringify({ error: 'Failed to check reminders', details: error }),
          { 
            status: 500,
            headers: {
              'Content-Type': 'application/json',
              'Access-Control-Allow-Origin': '*'
            }
          }
        )
      }

      return new Response(
        JSON.stringify({ 
          success: true,
          dueReminders: dueReminders || []
        }),
        { 
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          }
        }
      )
    }

    // If action is not recognized
    return new Response(
      JSON.stringify({ error: 'Invalid action' }),
      { 
        status: 400,
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