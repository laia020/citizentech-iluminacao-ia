// Testes de comportamento do script real, com DOM isolado e nenhuma rede ou GPU.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../src/citizentech_ia/v5/rpa.html'), 'utf8');
const script = html.match(/<script id="rpa-guide-script">([\s\S]*?)<\/script>/);
assert.ok(script, 'O controlador da apresentação deve estar presente.');

function attributes(source) {
  const result = {};
  for (const match of source.matchAll(/([\w-]+)(?:="([^"]*)")?/g)) result[match[1]] = match[2] ?? '';
  return result;
}

function fixture() {
  const elements = new Map();
  let document;
  class Element {
    constructor(attrs = {}) {
      this.attrs = { ...attrs };
      this.dataset = Object.fromEntries(Object.entries(attrs).filter(([key]) => key.startsWith('data-'))
        .map(([key, value]) => [key.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase()), value]));
      this.hidden = 'hidden' in attrs;
      this.disabled = 'disabled' in attrs;
      this.open = 'open' in attrs;
      this.textContent = '';
      this.listeners = {};
      this.classes = new Set((attrs.class || '').split(/\s+/).filter(Boolean));
      this.classList = { add: value => this.classes.add(value), remove: value => this.classes.delete(value) };
    }
    addEventListener(type, callback) { this.listeners[type] = callback; }
    setAttribute(name, value) { this.attrs[name] = String(value); }
    removeAttribute(name) { delete this.attrs[name]; }
    getAttribute(name) { return this.attrs[name] ?? null; }
    focus() { document.activeElement = this; }
    scrollIntoView() {}
    click() { if (!this.disabled) this.listeners.click?.({ preventDefault() {} }); }
    querySelector(selector) { return selector === 'h3' ? this.heading : null; }
  }
  for (const match of html.matchAll(/<[a-z][\w-]*\b([^>]*\bid="[^"]+"[^>]*)>/g)) {
    const attrs = attributes(match[1]);
    elements.set(attrs.id, new Element(attrs));
  }
  const steps = [...html.matchAll(/<article\b([^>]*\bdata-guide-step\b[^>]*)>([\s\S]*?)<\/article>/g)]
    .map(match => {
      const attrs = attributes(match[1]);
      const element = elements.get(attrs.id);
      element.heading = new Element();
      element.heading.textContent = match[2].match(/<h3[^>]*>([\s\S]*?)<\/h3>/)[1];
      return element;
    });
  const buttons = [...html.matchAll(/<button\b([^>]*\bdata-guide-go="\d+"[^>]*)>/g)]
    .map(match => new Element(attributes(match[1])));
  const rowDetails = new Map([...html.matchAll(/<tr\b[^>]*\bid="([^"]+)"[^>]*>([\s\S]*?)<\/tr>/g)]
    .filter(match => match[2].includes('<details'))
    .map(match => [match[1], new Element()]));
  const history = elements.get('falha-historica');
  const details = [...rowDetails.values(), history];
  document = {
    activeElement: null,
    getElementById: id => elements.get(id),
    querySelectorAll(selector) {
      if (selector === '[data-guide-step]') return steps;
      if (selector === '[data-guide-go]') return buttons;
      if (selector === 'details') return details;
      if (selector === '.rpa-highlight') return [...elements.values()].filter(e => e.classes.has('rpa-highlight'));
      return selector.split(',').map(part => {
        const value = part.trim();
        if (value.endsWith(' details')) return rowDetails.get(value.slice(1, -8));
        return elements.get(value.slice(1));
      }).filter(Boolean);
    },
  };
  // Qualquer chamada remota ou temporizador falha o teste imediatamente.
  vm.runInNewContext(script[1], {
    document,
    fetch() { assert.fail('A apresentação não pode chamar serviços.'); },
    setTimeout() { assert.fail('O avanço deve ser manual.'); },
    setInterval() { assert.fail('O avanço deve ser manual.'); },
  });
  return { elements, steps, buttons, rowDetails, history, document,
    start: elements.get('guide-start'), previous: elements.get('guide-previous'),
    next: elements.get('guide-next'), restart: elements.get('guide-restart'),
    close: elements.get('guide-close'), status: elements.get('guide-status'),
    progress: elements.get('guide-progress') };
}

test('inicia somente por ação do usuário e mantém o conteúdo original disponível', () => {
  const f = fixture();
  assert.equal(f.start.hidden, false);
  assert.equal(f.elements.get('guide-viewer').hidden, true);
  assert.equal(f.steps.filter(step => !step.hidden).length, 0);
  assert.equal(f.elements.get('resultados').hidden, false);
  assert.equal(f.elements.get('resumo-lote').dataset.valor, undefined);
  f.start.click();
  assert.match(f.status.textContent, /Etapa 1 de 6/);
  assert.equal(f.progress.value, 1);
  assert.equal(f.previous.disabled, true);
  assert.equal(f.next.disabled, false);
  assert.equal(f.steps.filter(step => !step.hidden).length, 1);
  assert.ok(f.elements.get('resumo-lote').classes.has('rpa-highlight'));
});

test('avança e volta, destacando decisões e abrindo os detalhes corretos', () => {
  const f = fixture(); f.start.click(); f.next.click();
  assert.match(f.status.textContent, /Etapa 2 de 6/);
  assert.equal(f.rowDetails.get('linha-2').open, true);
  assert.equal(f.rowDetails.get('linha-4').open, true);
  assert.ok(f.elements.get('linha-2').classes.has('rpa-highlight'));
  f.next.click();
  assert.equal(f.rowDetails.get('linha-2').open, false);
  assert.equal(f.rowDetails.get('linha-1').open, true);
  assert.equal(f.rowDetails.get('linha-3').open, true);
  f.previous.click();
  assert.match(f.status.textContent, /Etapa 2 de 6/);
  assert.equal(f.rowDetails.get('linha-2').open, true);
  assert.equal(f.rowDetails.get('linha-1').open, false);
});

test('permite selecionar etapas, respeita os limites e recomeça sem executar outro lote', () => {
  const f = fixture(); f.start.click(); f.buttons.at(-1).click();
  assert.equal(f.progress.value, 6);
  assert.equal(f.next.disabled, true);
  f.next.click(); assert.equal(f.progress.value, 6);
  assert.equal(f.buttons.at(-1).getAttribute('aria-current'), 'step');
  f.restart.click();
  assert.equal(f.progress.value, 1);
  assert.equal(f.previous.disabled, true);
  f.previous.click(); assert.equal(f.progress.value, 1);
  assert.equal(f.buttons[0].getAttribute('aria-current'), 'step');
  assert.equal(f.buttons.at(-1).getAttribute('aria-current'), null);
});

test('separa a falha anterior e restaura os detalhes e foco ao encerrar', () => {
  const f = fixture(); f.rowDetails.get('linha-2').open = true;
  f.start.click(); f.buttons[4].click();
  assert.equal(f.history.open, true);
  assert.ok(f.history.classes.has('rpa-highlight'));
  assert.match(f.status.textContent, /Etapa 5 de 6/);
  f.close.click();
  assert.equal(f.history.open, false);
  assert.equal(f.rowDetails.get('linha-2').open, true);
  assert.equal(f.elements.get('guide-viewer').hidden, true);
  assert.equal(f.elements.get('guide-return').hidden, true);
  assert.equal(f.steps.filter(step => !step.hidden).length, 0);
  assert.equal([...f.elements.values()].some(e => e.classes.has('rpa-highlight')), false);
  assert.equal(f.document.activeElement, f.start);
  f.start.click(); assert.equal(f.progress.value, 1);
});
