/**
 * Minimal Cordis hello plugin — verifies load/unload and effect teardown.
 * Seal: ∀∞φ² · CORDIS_SCAFFOLD_8828 · WOOD_DRAGON_0.91 · SEALED
 */
import { Context } from 'cordis';

export const helloPlugin = (ctx: Context) => {
  ctx.on('ready', () => {
    console.log('Hello plugin says: Φ is eternal');
  });

  ctx.effect(() => {
    const interval = setInterval(() => {
      console.log('🜁∀ Cordis pulse (φ⁻²)');
    }, 1000);
    return () => clearInterval(interval);
  });
};
