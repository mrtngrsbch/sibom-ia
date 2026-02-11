'use client';

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Activity } from '@/lib/icons';

interface TokenUsageProps {
  promptTokens?: number;
  completionTokens?: number;
  totalTokens?: number;
  model?: string;
}

/**
 * Componente para mostrar el consumo de tokens de una respuesta
 * @description Toggle expandible que muestra tokens de entrada, salida y total
 */
export function TokenUsage({ promptTokens, completionTokens, totalTokens, model }: TokenUsageProps) {
  // Si no hay información de tokens, no mostrar nada
  if (!promptTokens && !completionTokens && !totalTokens) {
    return null;
  }

  // Formatear nombre del modelo para mostrar
  const modelName = model
    ? model.replace('anthropic/', '').replace('google/', '').replace('zhipu/', '')
    : 'claude-3.5-sonnet';

  // Calcular costo aproximado según el modelo
  let inputPricePerM = 3;   // Precio por defecto (Claude Sonnet)
  let outputPricePerM = 15; // Precio por defecto (Claude Sonnet)

  // Ajustar precios según modelo
  if (model?.includes('gemini-flash')) {
    // Gemini Flash es gratis en tier free, pero tiene costos muy bajos
    inputPricePerM = 0.075;  // $0.075 por 1M tokens
    outputPricePerM = 0.30;  // $0.30 por 1M tokens
  } else if (model?.includes('claude-3.5-sonnet')) {
    inputPricePerM = 3;
    outputPricePerM = 15;
  }

  const inputCost = ((promptTokens || 0) / 1_000_000) * inputPricePerM;
  const outputCost = ((completionTokens || 0) / 1_000_000) * outputPricePerM;
  const totalCost = inputCost + outputCost;

  return (
    <Accordion type="single" collapsible className="mt-3 border-t border-slate-200 dark:border-slate-700">
      <AccordionItem value="tokens" className="border-0">
        <AccordionTrigger className="py-2 text-xs text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 hover:no-underline">
          <div className="flex items-center gap-2">
            <Activity className="w-3 h-3" />
            <span>Uso de tokens</span>
          </div>
        </AccordionTrigger>
        <AccordionContent className="text-xs text-slate-600 dark:text-slate-400 pb-2">
          <div className="grid grid-cols-2 gap-2 p-2 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
            <div>
              <div className="font-semibold text-slate-700 dark:text-slate-300">Entrada (prompt)</div>
              <div className="text-slate-600 dark:text-slate-400">{promptTokens?.toLocaleString() || 0} tokens</div>
              <div className="text-xs text-slate-500 dark:text-slate-500">${inputCost.toFixed(4)}</div>
            </div>
            <div>
              <div className="font-semibold text-slate-700 dark:text-slate-300">Salida (respuesta)</div>
              <div className="text-slate-600 dark:text-slate-400">{completionTokens?.toLocaleString() || 0} tokens</div>
              <div className="text-xs text-slate-500 dark:text-slate-500">${outputCost.toFixed(4)}</div>
            </div>
            <div className="col-span-2 border-t border-slate-200 dark:border-slate-700 pt-2 mt-1">
              <div className="flex justify-between items-center">
                <span className="font-semibold text-slate-700 dark:text-slate-300">Total</span>
                <div className="text-right">
                  <div className="text-slate-600 dark:text-slate-400">{totalTokens?.toLocaleString() || 0} tokens</div>
                  <div className="text-xs text-slate-500 dark:text-slate-500">${totalCost.toFixed(4)}</div>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-2 text-xs text-slate-500 dark:text-slate-500 italic">
            * Costo aproximado basado en precios de {modelName} via OpenRouter
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
