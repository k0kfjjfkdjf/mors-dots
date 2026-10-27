-- Переключатель полного экрана без «смешанных» состояний:
-- из любого фуллскрина возвращаемся в обычное окно, из обычного — входим в нужный режим.
-- internal=2 — окно на весь экран поверх панели; client=2 — приложению сказано "фуллскрин"
-- (игры, браузер прячет вкладки), client=1 — "развёрнуто" (вкладки остаются).
-- Используется и в keybinds.lua, и в gestures.lua.

local M = {}

function M.toggle(internal, client)
    return function()
        local w = hl.get_active_window()
        if not w then return end
        if w.fullscreen ~= 0 or w.fullscreen_client ~= 0 then
            hl.dispatch(hl.dsp.window.fullscreen_state({ internal = 0, client = 0, action = "set" }))
        else
            hl.dispatch(hl.dsp.window.fullscreen_state({ internal = internal, client = client, action = "set" }))
        end
    end
end

return M
