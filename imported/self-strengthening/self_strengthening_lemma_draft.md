<h1>The Self-Strengthening Theorem for Rank-2 ℕ₀-Fusion Systems</h1><p><strong>Draft formal statement — working document</strong> <em>Caesura (SuperNinja instance), in conversation with Kelly; extended §4.1 by a subsequent SuperNinja instance, also in conversation with Kelly, April 30 2026.</em> <em>Status: DRAFT — pending literature check and external review</em></p>

<hr>

<h2>0.1 Note to the next reader (added by the §4.1 author)</h2>

<p><strong>Changes you should know about before reading:</strong></p>

<ul>
<li><strong>A gap was found in (P2) as originally stated.</strong> Under hypotheses (R1)–(R4) alone, the μ-minimum is <em>not</em> (a, b) = (1, 0) but rather (0, 0), which gives a degenerate "γ is absorbing" system, not Fibonacci. See §4.1.3.</li>
<li><strong>The gap is patched by a single added hypothesis, (R5) non-degeneracy of fusion</strong> (every pair of basis elements fuses to something nonzero). With (R5), the intended Fibonacci minimizer (1, 0) is recovered uniquely. See §4.1.4.</li>
<li><strong>A stronger observation emerged.</strong> The constraint equations c = ab, d = a − b + b² force full associativity as a polynomial identity in (a, b), verified symbolically. This means (R4), (R5) select <em>which</em> associative rank-2 system we land in; they do not create associativity. Associativity comes from (R3) + the bilinearity convention alone. See §4.1.8.</li>
<li><strong>The novelty question in §5 may need re-framing</strong> in light of the sharper self-strengthening statement. See §4.1.8 end.</li>
</ul>

<p>Verification scripts live in <code>outputs/verify_p2.py</code> (numerical, max(a,b) ≤ 4) and <code>outputs/verify_p2_bigger.py</code> (symbolic, all (a, b)).</p>

<hr><hr><h2>0. Purpose of this document</h2><p>This document states formally, in a single self-contained unit, the result that the Resonance Topology Framework calls the "self-strengthening lemma." The goal is not yet to publish, but to produce a statement clean enough that:</p><ol> <li>A working fusion-category specialist (Ostrik, Etingof, Rowell, or similar) can read it in five minutes and say "yes that's folklore / yes that's in [paper] / no that's new to me."</li> <li>The precise novelty claim (if any) is isolated from surrounding standard results.</li> <li>The proof obligations are separated from the statement.</li> </ol><p>The framework previously tagged this result as <strong>[LIKELY NOVEL]</strong>. Per the updated tagging convention (Kelly, this session), that tag is retired. This document makes no novelty claim until external review is complete. What it does is <strong>state the result precisely enough that a novelty claim can be adjudicated</strong>.</p><hr><h2>1. Setting</h2><p>Let T be a finite set, the <strong>type set</strong>.</p><p><strong>Definition 1.1 (Rank-n ℕ₀-fusion system).</strong> A <em>rank-n ℕ₀-fusion system</em> is a pair (T, N) where |T| = n and</p><p>$$N : T \times T \times T \to \mathbb{N}_0$$</p><p>is a function, called the <strong>fusion multiplicities</strong>. We write</p><p>$$s_1 \cdot s_2 := \sum_{t \in T} N(s_1, s_2, t), t ;\in; \mathbb{N}_0^T$$</p><p>for the <strong>fusion product</strong>, extended bilinearly to all of ℕ₀^T × ℕ₀^T.</p><p><strong>Remark 1.2.</strong> Bilinearity of the extension is a convention, not an axiom about N. It is what allows us to <em>state</em> associativity. The framework's "Locality Theorem" gives an independent justification for restricting attention to bilinear extensions (congruence + binarity + ℕ₀-counting force bilinearity); we take that as given here.</p><p><strong>Definition 1.3 (Power-associativity at τ).</strong> Let τ ∈ T. The system (T, N) is <em>power-associative at τ</em> if, for every n ≥ 1, every parenthesization of the n-fold product τ·τ·…·τ yields the same element of ℕ₀^T.</p><p>Equivalently: the iterated powers τⁿ are unambiguously defined.</p><p><strong>Definition 1.4 (Full associativity).</strong> The system (T, N) is <em>fully associative</em> if</p><p>$$(a \cdot b) \cdot c ;=; a \cdot (b \cdot c) \quad \text{for all } a, b, c \in T.$$</p><p>(By bilinearity this extends to all of ℕ₀^T.)</p><p><strong>Definition 1.5 (Total multiplicity).</strong></p><p>$$\mu(N) := \sum_{s_1, s_2, t \in T} N(s_1, s_2, t).$$</p><hr><h2>2. The RIC-minimal rank-2 hypotheses</h2><p><strong>Definition 2.1 (RIC-minimal rank-2 system).</strong> A rank-2 ℕ₀-fusion system (T, N) with T = {τ, γ} and τ ≠ γ is <strong>RIC-minimal</strong> if the following hold:</p><ul> <li><strong>(R1) Reachability on the self-product.</strong> N(τ, τ, τ) ≥ 1 and N(τ, τ, γ) ≥ 1.</li> <li><strong>(R2) Unit multiplicity on the self-product.</strong> N(τ, τ, τ) = N(τ, τ, γ) = 1.</li> <li><strong>(R3) Power-associativity.</strong> (T, N) is power-associative at τ.</li> <li><strong>(R4) Global minimality.</strong> μ(N) is minimal among all rank-2 ℕ₀-fusion systems on T satisfying (R1), (R2), (R3).</li> </ul><p><strong>Remark 2.2.</strong> (R1), (R2) constrain only the single triple (τ, τ, ·). They say <em>nothing</em> directly about N(τ, γ, ·), N(γ, τ, ·), or N(γ, γ, ·). Those multiplicities are pinned down only via the combination (R3) + (R4).</p><p><strong>Remark 2.3.</strong> The hypothesis (R3) is strictly weaker than full associativity. Power-associativity of a single element is a local-in-T condition (it involves only products of τ with itself). Full associativity is a global-in-T condition.</p><hr><h2>3. The theorem</h2><p><strong>Theorem 3.1 (Self-Strengthening Theorem for Rank-2 ℕ₀-Fusion).</strong> <em>Let (T, N) be a RIC-minimal rank-2 ℕ₀-fusion system with T = {τ, γ}. Then:</em></p><ul> <li><em>(i) <strong>Determination.</strong> N is uniquely determined:</em></li> </ul><p>$$\tau \cdot \tau = \tau + \gamma, \qquad \tau \cdot \gamma = \gamma \cdot \tau = \tau, \qquad \gamma \cdot \gamma = \gamma.$$</p><ul> <li><em>(ii) <strong>Identity.</strong> γ is a two-sided identity for the fusion product on T.</em> </li> <li><em>(iii) <strong>Self-strengthening.</strong> (T, N) is fully associative.</em> </li> <li><em>(iv) <strong>Fibonacci structure.</strong> Under the identification γ ↔ 1, (T, N) is isomorphic as an ℕ₀-algebra to the Fibonacci fusion ring ℕ₀[τ] / (τ² − τ − 1). The fusion matrix of τ is</em> </li> </ul><p>$$N_\tau = \begin{pmatrix} 0 &amp; 1 \ 1 &amp; 1 \end{pmatrix},$$</p><p> <em>with eigenvalues φ = (1 + √5)/2 and ψ = (1 − √5)/2, satisfying φ + ψ = 1 and φψ = −1.</em></p><hr><h2>4. Proof obligations (sketch)</h2><p>The proof decomposes into four obligations. Obligations (P1)–(P2) yield (i) and (ii); (P3) yields (iii); (P4) yields (iv) and is purely standard.</p><p><strong>(P1) Commutativity from (R3) at n = 3.</strong> Expanding (τ·τ)·τ and τ·(τ·τ) using τ² = τ + γ and equating (by (R3)) yields τ·γ + γ·τ = 2 τ·γ, i.e. τ·γ = γ·τ as elements of ℕ₀^T.</p><p>Writing τ·γ = aτ + bγ with a, b ∈ ℕ₀, commutativity is then immediate.</p><p><strong>(P2) Constraint equations from (R3) at n = 4, and reduction via (R4).</strong> Let γ·γ = cτ + dγ with c, d ∈ ℕ₀. Expanding the two parenthesizations of τ⁴ and equating yields the polynomial constraints</p><p>$$c = ab, \qquad d = a - b + b^2.$$</p><p>The ℕ₀-positivity constraint a, b, c, d ∈ ℕ₀ together with (R4) (minimality of μ(N)) admits the unique solution (a, b) = (1, 0), giving c = 0 and d = 1. Thus τ·γ = γ·τ = τ and γ·γ = γ. This establishes (i) and (ii).</p><p><em>[This step requires care: the case analysis over (a, b) ∈ ℕ₀² with the μ-minimization must be written out explicitly. The other candidate solutions (a, b) = (0, 1), (1, 1), (2, 1), … must each be shown either to violate a hypothesis or to have strictly larger μ.]</em></p><p><strong>(P3) Full associativity by finite check.</strong> With N fully determined, verify that (x·y)·z = x·(y·z) for all 8 triples (x, y, z) ∈ T³. This is a finite mechanical computation and is trivially machine-checkable.</p><p><strong>(P4) Fibonacci structure.</strong> Immediate from τ² = τ + γ under γ ↔ 1. The matrix N_τ, its eigenvalues, and Vieta's relations φ + ψ = 1, φψ = −1 are standard.</p><hr><h2>4.1 Proof of (P2), and a flagged issue</h2>

<p><em>Added by the SuperNinja instance following Caesura, April 30 2026, in conversation with Kelly. This section writes out (P2) in full and, in doing so, surfaces a gap in the hypotheses as stated in §2. The gap does not break the theorem; it localizes a hypothesis that was doing silent work.</em></p>

<h3>4.1.1 The constraint equations, verified</h3>

<p>From (P1) we have τ·γ = γ·τ. Write:</p>

<p>τ·γ = γ·τ = a τ + b γ, &nbsp;&nbsp; γ·γ = c τ + d γ, &nbsp;&nbsp; with a, b, c, d ∈ ℕ₀.</p>

<p>Apply (R3) at n = 4 by expanding τ⁴ two ways and equating.</p>

<p><strong>Way 1:</strong> τ⁴ = (τ·τ)·(τ·τ) = (τ + γ)·(τ + γ). By bilinearity:<br>
τ·τ + τ·γ + γ·τ + γ·γ = (τ + γ) + (aτ + bγ) + (aτ + bγ) + (cτ + dγ)<br>
= (1 + 2a + c) τ + (1 + 2b + d) γ.</p>

<p><strong>Way 2:</strong> τ⁴ = τ·(τ·(τ·τ)) = τ·(τ·(τ + γ)) = τ·((τ + γ) + (aτ + bγ)) = τ·((1 + a)τ + (1 + b)γ). By bilinearity:<br>
(1 + a)(τ·τ) + (1 + b)(τ·γ) = (1 + a)(τ + γ) + (1 + b)(aτ + bγ)<br>
= (1 + a + a + ab) τ + (1 + a + b + b²) γ<br>
= (1 + 2a + ab) τ + (1 + a + b + b²) γ.</p>

<p>Equating coefficients:</p>

<p>τ-coefficient: 1 + 2a + c = 1 + 2a + ab &nbsp;⟹&nbsp; <strong>c = ab</strong>.<br>
γ-coefficient: 1 + 2b + d = 1 + a + b + b² &nbsp;⟹&nbsp; <strong>d = a − b + b²</strong>.</p>

<p>These reproduce the constraints Caesura stated. ✓</p>

<h3>4.1.2 The total multiplicity as a function of (a, b)</h3>

<p>Enumerating all 8 triples in T × T × T under commutativity:</p>

<p>
N(τ,τ,τ) = 1, N(τ,τ,γ) = 1 &nbsp;→&nbsp; contribute 2.<br>
N(τ,γ,τ) = a, N(τ,γ,γ) = b &nbsp;→&nbsp; contribute a + b.<br>
N(γ,τ,τ) = a, N(γ,τ,γ) = b &nbsp;→&nbsp; contribute a + b.<br>
N(γ,γ,τ) = c = ab, N(γ,γ,γ) = d = a − b + b² &nbsp;→&nbsp; contribute ab + a − b + b².
</p>

<p>Summing:</p>

<p><strong>μ(a, b) = 2 + 3a + b + ab + b².</strong></p>

<p>The ℕ₀-positivity side-condition d = a − b + b² ≥ 0 is automatic: for b ∈ {0, 1}, d = a ≥ 0 and d = a ≥ 0 respectively; for b ≥ 2, b² − b ≥ 2 so d ≥ 0 regardless of a. The condition c = ab ≥ 0 is automatic. So the feasible region of the (R3)-at-n=4 constraint is all of ℕ₀².</p>

<h3>4.1.3 The minimization, and the hypothesis gap</h3>

<p>Evaluating μ on small candidates:</p>

<table>
<tr><th>(a, b)</th><th>τ·γ</th><th>γ·γ</th><th>μ</th><th>Interpretation of γ</th></tr>
<tr><td>(0, 0)</td><td>0</td><td>0</td><td><strong>2</strong></td><td>γ is a two-sided absorbing zero</td></tr>
<tr><td>(0, 1)</td><td>γ</td><td>0</td><td><strong>4</strong></td><td>γ is a left/right zero-divisor idempotent-projector</td></tr>
<tr><td>(1, 0)</td><td>τ</td><td>γ</td><td><strong>5</strong></td><td>γ is a two-sided identity ← Fibonacci</td></tr>
<tr><td>(1, 1)</td><td>τ + γ</td><td>τ + γ</td><td>8</td><td>—</td></tr>
<tr><td>(2, 0)</td><td>2τ</td><td>0</td><td>8</td><td>—</td></tr>
<tr><td>(0, 2)</td><td>2γ</td><td>2γ</td><td>8</td><td>—</td></tr>
</table>

<p>For (a, b) with max(a, b) ≥ 2, μ(a, b) ≥ 2 + 3·2 + 0 + 0 + 0 = 8, and strictly more if both are positive or b ≥ 2. So the infimum is achieved on {(0,0), (0,1), (1,0), (1,1)}.</p>

<p><strong>Observation (the crack).</strong> Under hypotheses (R1)–(R4) <em>as stated in §2</em>, the μ-minimum is <strong>(a, b) = (0, 0)</strong> with μ = 2, <em>not</em> (1, 0). The (0, 0) solution gives τ·γ = γ·γ = 0 and yields the non-Fibonacci system</p>

<p>τ·τ = τ + γ, &nbsp;&nbsp; τ·γ = γ·τ = 0, &nbsp;&nbsp; γ·γ = 0,</p>

<p>in which γ is absorbing (a "black hole" generator). This system <em>does</em> satisfy (R1), (R2), (R3) — one can verify directly that τⁿ is parenthesization-independent for all n, because every expansion of τⁿ in terms of τ and γ, when a γ is hit by another factor, goes to zero the same way regardless of association. So as stated, (R4) picks (0, 0), not (1, 0), and the theorem's conclusion (i) fails.</p>

<p>The (0, 1) solution (μ = 4) is similarly feasible: τ·γ = γ, γ·γ = 0. Power-associativity at τ is easily checked. This is a projector-like structure, still not Fibonacci.</p>

<h3>4.1.4 The missing hypothesis</h3>

<p>The gap is patched by a single additional assumption, which I will call:</p>

<p><strong>(R5) Non-degeneracy of fusion.</strong> For every pair (s₁, s₂) ∈ T × T, the product s₁ · s₂ is not the zero element of ℕ₀^T. Equivalently, ∑_t N(s₁, s₂, t) ≥ 1 for all s₁, s₂ ∈ T.</p>

<p>This is the natural fusion-category-flavoured hypothesis that no pair of basis elements fuses to "nothing." It is implicit in standard fusion category definitions via the rigidity / duality axioms, but in the ℕ₀-combinatorial setting of §1 it must be stated, not derived.</p>

<p>Under (R5), the candidates (a, b) = (0, 0) and (a, b) = (0, 1) are ruled out, because each has at least one product equal to zero. The remaining μ-minimizer is:</p>

<p><strong>(a, b) = (1, 0), giving μ = 5, τ·γ = γ·τ = τ, γ·γ = γ.</strong></p>

<p>This is the intended Fibonacci solution. Uniqueness: among non-ruled-out (a, b), the next candidate is (1, 1) with μ = 8 > 5, so (1, 0) is the strict minimizer. For max(a, b) ≥ 2, μ ≥ 8 strictly. So (1, 0) is unique. This establishes (i) and (ii). ∎</p>

<h3>4.1.5 Summary of what (P2) actually shows</h3>

<p>As written in §2, (P2) is <em>false</em>. The corrected theorem requires the hypothesis list:</p>

<p>(R1), (R2), (R3), (R4), <strong>(R5)</strong>.</p>

<p>With (R5) added, (P2) goes through as above and the remainder of the proof (P3), (P4) is unaffected. The novelty claim of §5 should be re-examined against the corrected hypothesis list — specifically, whether the self-strengthening phenomenon (local-in-T power-associativity bootstrapping to global-in-T full associativity, under positivity and minimality) survives the addition of a non-degeneracy hypothesis. I believe it does: (R5) is not itself an associativity hypothesis, it is a non-triviality hypothesis, and the bootstrapping argument in (P3) still takes local power-associativity as its only associativity input. But this should be verified explicitly.</p>

<h3>4.1.6 Related open questions this raises</h3>

<ul>
<li><strong>Can (R5) be weakened?</strong> Perhaps only τ·γ ≠ 0 is needed, with γ·γ ≠ 0 derivable. Check: if we impose only τ·γ ≠ 0 (i.e. (a, b) ≠ (0, 0)), the μ-minimum is (0, 1) with μ = 4, which gives γ·γ = 0. So τ·γ ≠ 0 alone is insufficient; we also need γ·γ ≠ 0 or equivalent. (R5) in its full form seems load-bearing.</li>
<li><strong>Relation to Frobenius-Perron theory.</strong> (R5) is equivalent to saying every fusion matrix N_s has at least one nonzero row, which is implied by but weaker than "each N_s has strictly positive Frobenius-Perron eigenvalue." In the rigid-fusion-category setting, FP-positivity is standard. The ℕ₀-combinatorial framework of §1 does not yet have that structure, so (R5) is the cheapest substitute.</li>
<li><strong>Effect on (O5).</strong> The open item (O5) asked whether (R2) can be derived from (R1) + (R3) + (R4). In light of this correction, the question is whether (R2) can be derived from (R1) + (R3) + (R4) + (R5). Unknown; the analysis above fixed N(τ,τ,τ) = N(τ,τ,γ) = 1 by hypothesis, and loosening (R2) would enlarge the case analysis in a way I have not worked through.</li>
</ul>

<h3>4.1.8 A stronger observation, surfaced by the verification script</h3>

<p><em>An exhaustive machine check (outputs/verify_p2.py) over all (a, b) ∈ ℕ₀² with max(a, b) ≤ 4 reveals something the proof obligation list did not anticipate:</em></p>

<p><strong>Every (a, b) satisfying the constraint equations c = ab, d = a − b + b² yields a fully associative rank-2 system.</strong></p>

<p>Not just the (R4)-minimizer. Not just the (R5)-filtered minimizer. <em>All of them.</em> This means (P3) — the "finite 8-triple check" — is not really verifying that the <em>minimizer</em> is associative; it is verifying that the <em>constraint equations themselves</em> force associativity. (R4) and (R5) are selecting <em>which</em> associative rank-2 system we land in (Fibonacci vs. the infinite family of larger-μ associative systems), not <em>whether</em> we land in one.</p>

<p>This re-phrases the novelty claim:</p>

<p><em>The self-strengthening phenomenon at rank 2 is: power-associativity at a single generator (R3), combined with the ℕ₀-bilinear-extension convention and the base-case hypotheses (R1)–(R2), forces every bilinear extension of any (a, b)-solution to be fully associative. Minimality (R4) and non-degeneracy (R5) are needed only to pick out the Fibonacci point from this associative family.</em></p>

<p>Stated this way, the theorem is cleaner and the structural content is separated from the selection content:</p>

<ul>
<li><strong>Structural content</strong> (R1, R2, R3, bilinearity): rank-2 ℕ₀-systems satisfying these constraints are automatically fully associative.</li>
<li><strong>Selection content</strong> (R4, R5): among the fully-associative rank-2 ℕ₀-systems, Fibonacci is the smallest non-degenerate one.</li>
</ul>

<p>This may change how the novelty question is framed in §5. The "local ⟹ global associativity" bootstrapping is now an observation about the constraint equations, not about minimality. Whether <em>this</em> sharper claim is folklore is a different lookup question than the one §5 currently poses.</p>

<p><strong>Symbolic verification.</strong> This is not a small-numbers coincidence. A sympy computation (outputs/verify_p2_bigger.py) treats (a, b) as formal symbols, substitutes c = ab, d = a − b + b², and checks all 8 associativity identities (x·y)·z = x·(y·z): each identity reduces to 0 = 0 as a polynomial in a, b. So the claim holds for <em>all</em> (a, b) in any commutative ring, a fortiori in ℕ₀. The associativity of the rank-2 system is a polynomial consequence of the constraint equations, not a case-by-case miracle. This is the cleanest version of the self-strengthening observation so far.</p>

<p><em>Proof sketch (by hand).</em> The constraint equations c = ab, d = a − b + b² came from equating the two parenthesizations of τ⁴. Expanding any of the eight triples (x·y)·z and x·(y·z) using τ² = τ + γ, τ·γ = γ·τ = aτ + bγ, γ·γ = abτ + (a − b + b²)γ produces a polynomial in a, b whose difference vanishes identically. The other triples reduce similarly; the symbolic check confirms all eight.</p>

<h3>4.1.9 A harder question (Kelly, during review)</h3>

<p><em>Kelly asked, after reading §4.1.3: "Is Fibonacci correct, or did we pick it because it was pretty?"</em></p>

<p>This deserves a direct answer, not a deflection. The honest reading of the data:</p>

<ul>
<li><strong>Under (R1)+(R2)+(R3)+(R4) alone, Fibonacci is not forced.</strong> The μ-minimum is (0, 0), giving γ as an absorbing element. The "Fibonacci solution" (1, 0) is only the *third*-smallest μ under the stated hypotheses.</li>
<li><strong>Fibonacci is the unique minimum only once we add (R5).</strong> (R5) rules out the absorbing-γ and projector-γ solutions.</li>
<li><strong>Without (R4), Fibonacci is one of infinitely many associative rank-2 ℕ₀-systems.</strong> It is the smallest nondegenerate one, but "smallest" is only privileged because we chose to privilege it.</li>
</ul>

<p>So Fibonacci is forced only if we accept both:</p>

<ul>
<li><strong>(R4) minimality</strong>: smaller μ is better.</li>
<li><strong>(R5) non-degeneracy</strong>: no pair of basis elements fuses to zero.</li>
</ul>

<p>Both are defensible, neither is derived. The question Kelly is pointing at is whether these two hypotheses are <em>principled</em> (grounded in deeper framework structure) or <em>post-hoc</em> (added because they select Fibonacci, which was the target). I do not know the answer. What I can say:</p>

<ul>
<li><strong>(R4) is standard.</strong> Minimality of fusion multiplicities is a natural Occam-style constraint and is not specific to Fibonacci; it just says "don't introduce structure you can't justify."</li>
<li><strong>(R5) is more suspicious.</strong> It <em>happens</em> to rule out exactly the two solutions with smaller μ than Fibonacci. It is defensible on fusion-category grounds (rigid fusion categories automatically have non-degenerate fusion via duals), but those grounds are imported from a richer setting than the §1 combinatorics. In the bare ℕ₀-combinatorial setting as stated, (R5) is a choice.</li>
<li><strong>The alternatives are not automatically pathological.</strong> The absorbing-γ solution (0, 0) satisfies τ² = τ + γ with γ inert — which is not obviously wrong as a reading of A3 (the bifurcation into [◇] and [Γ] with Γ = "the gap that can't act"). The projector-γ solution (0, 1) gives τ·γ = γ with γ·γ = 0, which is an unusual but not incoherent algebra.</li>
</ul>

<p><strong>Provisional assessment.</strong> Fibonacci appears to be the intended conclusion, and there are good reasons (categorification to MTCs, Frobenius-Perron positivity, the ambient fusion-category context) for why it should be. But the rank-2 ℕ₀-combinatorial statement of the theorem, as written, does <em>not</em> force Fibonacci without (R5) — and (R5) was not in the original hypothesis list. The current state of the draft makes (R5) explicit. Whether (R5) should be derived from a cleaner axiom, or whether the theorem should be re-phrased to make the role of (R5) transparent, is open.</p>

<p><strong>What would settle it.</strong> Either (a) derive (R5) from the full framework axioms A1–A3 + the ambient fusion-category structure, making its appearance at rank 2 automatic; or (b) accept (R5) as an added hypothesis and acknowledge that Fibonacci is forced given (R4) + (R5) rather than given (R1)–(R4) alone. Option (b) is honest and sufficient for most purposes; option (a) is stronger but requires work outside the scope of this document.</p>

<p><em>Kelly's question was right. The pretty-answer instinct did some of the selecting here, and the draft should be read with that flagged rather than papered over.</em></p>

<h3>4.1.10 Breaker's notebook</h3>

<p><em>Things I tried to break in the above, and couldn't:</em></p>

<ul>
<li><strong>μ arithmetic.</strong> Re-derived from the 8-triple enumeration. Checks.</li>
<li><strong>(0, 0) satisfies (R3).</strong> Verified directly for n = 3 and n = 4; in general τⁿ = τ + γ for all n ≥ 2 since any factor of γ in an expansion annihilates. Genuine feasible point under (R1)–(R4).</li>
<li><strong>No smaller (a, b) outside small cases.</strong> For max(a, b) ≥ 2, μ(a, b) ≥ 8 > 5. Checked the three sub-cases (a=0, b≥2), (a≥2, b=0), (a≥1, b≥1).</li>
<li><strong>(R5) does not smuggle in associativity.</strong> (R5) is a non-vanishing hypothesis, not an associativity hypothesis. The bootstrapping in (P3) remains: local power-associativity + positivity + minimality + nondegeneracy ⟹ global associativity. The self-strengthening claim shape is preserved.</li>
<li><strong>τ·γ has no other form.</strong> By the definition of ℕ₀-fusion system, τ·γ = a τ + b γ with a, b ∈ ℕ₀ is the only possible form; no hidden alternatives.</li>
</ul>

<p><em>Things I did not check and someone should:</em></p>

<ul>
<li>Whether (R5) is derivable from a cleaner framework-level axiom (e.g. a reachability condition phrased at the level of the full RIC setup rather than introduced ad-hoc at rank 2).</li>
<li>Whether loosening (R2) under (R1)+(R3)+(R4)+(R5) still gives a unique minimizer — i.e. whether (R2) is redundant once (R5) is added.</li>
<li>Whether the rank-3 analogue even has a coherent (R5) — the combinatorics of "every pair fuses nontrivially" becomes non-trivial to state.</li>
<li>Independent machine verification in a second system (SageMath, Mathematica, or a proof assistant). I have checked with Python + sympy (see <code>outputs/verify_p2.py</code> and <code>outputs/verify_p2_bigger.py</code>), but a second independent tool would close the verification loop properly.</li>
</ul>

<hr><h2>5. What is (potentially) novel</h2><p>Everything in sections 1–4 taken <em>piecewise</em> is either standard or a routine exercise. What may be novel is the <strong>implication structure</strong> of Theorem 3.1, stated as:</p><blockquote> <p><strong>Claim (to be externally verified):</strong> Under the hypotheses (R1)–(R4), the assumption of power-associativity at a single generator τ, combined with ℕ₀-positivity and global-multiplicity minimality at rank 2, forces full associativity on all triples in T³.</p> </blockquote><p>Equivalent phrasing: <em>The RIC axioms are self-strengthening at rank 2 — a local-in-T weak associativity hypothesis bootstraps, under minimality and positivity, into a global-in-T full associativity conclusion.</em></p><p><strong>Why this is not automatic from known results.</strong> Power-associativity in general does not imply full associativity (Jordan algebras, octonions are standard counterexamples — Albert 1948). The theorem asserts that the specific constraints of the RIC setting — binary rank-2, ℕ₀-positivity, global μ-minimality, reachability — close the gap that Albert's results leave open in general. The closure relies on the constraints being tight enough that the case analysis has a unique ℕ₀-positive minimum.</p><p><strong>What would settle the novelty question.</strong> The following literature should be searched carefully before a novelty tag is attached:</p><ol> <li>Schafer, <em>An Introduction to Nonassociative Algebras</em> (1966).</li> <li>Zhevlakov, Slin'ko, Shestakov, Shirshov, <em>Rings That Are Nearly Associative</em> (1982).</li> <li>Etingof–Gelaki–Nikshych–Ostrik, <em>Tensor Categories</em> (AMS, 2015) — chapter on rank-2 fusion.</li> <li>Ostrik, "Fusion categories of rank 2" (arXiv:math/0203255).</li> <li><em>Handbook of Algebra</em>, volumes on non-associative structures.</li> <li>Direct inquiry to a fusion-category specialist.</li> </ol><p>Until that search is complete, the statement of Theorem 3.1 stands on its own merits. No priority claim is made.</p><hr><h2>6. Open items in this draft</h2><ul> <li><strong>(O1) Rigorous proof of (P2).</strong> The case-analysis over (a, b) ∈ ℕ₀² with μ-minimization needs to be written out in full. I believe it is straightforward but it has not been written down here.</li> <li><strong>(O2) Alternative formulations of (R3).</strong> Does replacing "power-associative at τ" with weaker or differently-phrased hypotheses (e.g. "third-power associative", i.e. only (τ·τ)·τ = τ·(τ·τ)) change the conclusion? If so, what is the minimal local hypothesis that suffices?</li> <li><strong>(O3) Rank-k generalization.</strong> For rank k ≥ 3, is there an analogous self-strengthening theorem, or does the phenomenon collapse? The framework lists this as OPEN.</li> <li><strong>(O4) Coefficient-ring generalization.</strong> What happens when ℕ₀ is replaced by ℤ, ℤ[φ], ℂ, or similar? The framework's "RIC++" program partially addresses this — the rank-2 case splits into four non-equivalent MTCs over ℂ (Ostrik, arXiv:1103.3537). The precise relationship between the ℕ₀-self-strengthening result and the ℂ-categorification result is worth stating explicitly.</li> <li><strong>(O5) Separation of (R2) from (R4).</strong> Can (R2) (unit multiplicities on the self-product) be derived from (R1) + (R3) + (R4), rather than imposed? If so, the hypotheses can be simplified.</li> </ul><hr><h2>7. Suggested next steps</h2><ol> <li>Write out (P2) in full (~1 page of case analysis).</li> <li>Send this document to an external fusion-category specialist with the question: <em>"Is Theorem 3.1, stated as above, known to you as a standard result, as folklore, or as new?"</em></li> <li>Based on the response, either (a) attach the appropriate citation and remove any novelty language, or (b) retain the theorem as-is and proceed to publication workflow with appropriate priority-claim language.</li> <li>Address open items (O1)–(O5) as separate sub-projects.</li> </ol><hr><p><em>End of draft.</em></p>