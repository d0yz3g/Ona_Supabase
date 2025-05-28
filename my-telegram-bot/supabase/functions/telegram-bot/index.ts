import { serve, Bot, createClient } from "./deps.ts";
import { setupCommands } from "./commands.ts";
import { setupOnboarding } from "./onboarding.ts";

// Создаем экземпляр бота с использованием токена из переменных окружения
const bot = new Bot(Deno.env.get("TELEGRAM_BOT_TOKEN")!);
await bot.init(); // <-- Обязательный вызов


const supabase = createClient(
  Deno.env.get("SB_URL")!,
  Deno.env.get("SB_ANON_KEY")!
);


// Обработка команды /start
bot.command("start", async (ctx) => {
  try {
    if (!ctx.from) {
      await ctx.reply("Не удалось определить пользователя.");
      return;
    }

    // Сохраняем информацию о пользователе в Supabase
    const { data: existingUser, error: checkError } = await supabase
      .from("users")
      .select("id")
      .eq("id", ctx.from.id)
      .single();

    if (!existingUser) {
      // Новый пользователь - создаем запись
      const { error: insertError } = await supabase
        .from("users")
        .insert({
          id: ctx.from.id,
          name: ctx.from.first_name,
          username: ctx.from.username,
          last_seen: new Date(),
          created: new Date(),
          is_onboarding_complete: false
        });

      if (insertError) {
        console.error("Ошибка при создании пользователя:", insertError);
        await ctx.reply("Произошла ошибка при запуске бота. Пожалуйста, попробуйте позже.");
        return;
      }

      // Отправляем приветственное сообщение новому пользователю
      await ctx.reply(
        `Привет, ${ctx.from.first_name || "пользователь"}! Добро пожаловать в бот с Supabase интеграцией.\n\n` +
        `Для начала рекомендуем пройти онбординг, чтобы создать ваш персональный профиль. ` +
        `Используйте команду /onboarding, чтобы начать.`
      );
    } else {
      // Существующий пользователь - обновляем время последнего посещения
      const { error: updateError } = await supabase
        .from("users")
        .update({ last_seen: new Date() })
        .eq("id", ctx.from.id);

      if (updateError) {
        console.error("Ошибка при обновлении пользователя:", updateError);
      }

      // Получаем информацию о статусе онбординга
      const { data: userData, error: userError } = await supabase
        .from("users")
        .select("is_onboarding_complete")
        .eq("id", ctx.from.id)
        .single();

      if (userError) {
        console.error("Ошибка при получении информации о пользователе:", userError);
      }

      // Отправляем приветственное сообщение существующему пользователю
      if (userData?.is_onboarding_complete) {
        await ctx.reply(
          `С возвращением, ${ctx.from.first_name || "пользователь"}!\n\n` +
          `Используйте команду /help, чтобы увидеть список доступных команд.`
        );
      } else {
        await ctx.reply(
          `С возвращением, ${ctx.from.first_name || "пользователь"}!\n\n` +
          `Похоже, вы еще не завершили онбординг. Используйте команду /onboarding, чтобы создать ваш персональный профиль.`
        );
      }
    }
  } catch (err) {
    console.error("Ошибка в обработчике /start:", err);
    await ctx.reply("Произошла ошибка при запуске бота. Пожалуйста, попробуйте позже.");
  }
});

// Настраиваем дополнительные команды бота
setupCommands(bot, supabase);

// Настраиваем функционал онбординга и профилирования
setupOnboarding(bot, supabase);

// Обработка middleware для логирования взаимодействий
bot.use(async (ctx, next) => {
  console.log(`Новое сообщение от пользователя ${ctx.from?.id}: ${ctx.message?.text}`);
  
  // Обновляем время последнего взаимодействия пользователя с ботом
  if (ctx.from?.id) {
    await supabase
      .from("users")
      .update({ last_seen: new Date() })
      .eq("id", ctx.from.id)
      .then(({ error }) => {
        if (error) console.error("Ошибка при обновлении last_seen:", error);
      });
  }
  
  await next();
});

// Обрабатываем входящие обновления с помощью webhook
serve(async (req) => {
  try {
    const update = await req.json();
    await bot.handleUpdate(update);
    return new Response("OK", { status: 200 });
  } catch (err) {
    console.error("Ошибка при обработке запроса:", err);
    return new Response("Ошибка при обработке запроса", { status: 500 });
  }
}); 